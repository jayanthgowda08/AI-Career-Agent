"""
services/semantic_search.py — Semantic and Hybrid Search Engine

Implements:
1. Embedding generation and storage for all jobs using pgvector.
2. Semantic similarity search via pgvector cosine distance operator (<=>).
3. Hybrid Search combining vector cosine similarity with SQL text matching.
4. Explanatory match reasons for each retrieved job.
"""

from typing import List, Tuple
from loguru import logger
from sqlalchemy import or_, select, and_
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_embedding import JobEmbedding
from app.schemas.search import SemanticSearchRequest, ScoredJobResponse
from app.schemas.job import JobResponse
from app.services.embedding_service import embed_text, embed_batch


def prepare_job_text_for_embedding(job: Job) -> str:
    """
    Constructs a rich textual representation of a job listing
    combining title, company, description, and required skills.
    """
    skills_text = ", ".join(job.required_skills) if job.required_skills else "None specified"
    pref_skills = ", ".join(job.preferred_skills) if job.preferred_skills else ""
    
    parts = [
        f"Job Title: {job.title}",
        f"Company: {job.company}",
        f"Location: {job.location}",
        f"Experience Level: {job.experience_level}",
        f"Required Skills: {skills_text}",
    ]
    if pref_skills:
        parts.append(f"Preferred Skills: {pref_skills}")
    parts.append(f"Description:\n{job.description}")
    
    return "\n".join(parts)


def ensure_all_jobs_embedded(db: Session) -> Tuple[int, int]:
    """
    Finds all jobs that do not yet have an embedding in job_embeddings,
    computes their embeddings in batch, and stores them.
    Returns (embedded_count, total_jobs).
    """
    # Find jobs missing embeddings
    subquery = select(JobEmbedding.job_id)
    jobs_without_embeddings = db.query(Job).filter(~Job.id.in_(subquery)).all()
    total_jobs = db.query(Job).count()

    if not jobs_without_embeddings:
        logger.info(f"All {total_jobs} jobs already have embeddings.")
        return 0, total_jobs

    logger.info(f"Generating embeddings for {len(jobs_without_embeddings)} un-indexed jobs...")
    texts = [prepare_job_text_for_embedding(job) for job in jobs_without_embeddings]
    vectors = embed_batch(texts)

    for job, vector in zip(jobs_without_embeddings, vectors):
        emb_record = JobEmbedding(job_id=job.id, embedding=vector)
        db.add(emb_record)

    db.commit()
    logger.info(f"✅ Generated and saved {len(jobs_without_embeddings)} job embeddings.")
    return len(jobs_without_embeddings), total_jobs


def search_jobs_semantic(
    db: Session,
    request: SemanticSearchRequest,
) -> List[ScoredJobResponse]:
    """
    Pure Semantic Vector Search using pgvector cosine distance (<=>).
    Returns top-K jobs ordered by highest cosine similarity.
    """
    # 1. Ensure all jobs have embeddings
    ensure_all_jobs_embedded(db)

    # 2. Embed user query
    query_vector = embed_text(request.query)

    # 3. Build query using pgvector cosine distance: JobEmbedding.embedding.cosine_distance(query_vector)
    distance_col = JobEmbedding.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        select(Job, distance_col)
        .join(JobEmbedding, Job.id == JobEmbedding.job_id)
    )

    # Apply optional structured filters
    conditions = []
    if request.location:
        conditions.append(Job.location.ilike(f"%{request.location}%"))
    if request.employment_type:
        conditions.append(Job.employment_type.ilike(request.employment_type))
    if request.experience_level:
        conditions.append(Job.experience_level.ilike(request.experience_level))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Order by nearest distance and limit top_k
    stmt = stmt.order_by("distance").limit(request.top_k)
    results = db.execute(stmt).all()

    scored_jobs = []
    for job, distance in results:
        # Convert cosine distance to cosine similarity: similarity = 1 - distance
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        
        # Generate explanatory reason
        reasons = [f"Semantic match: {int(similarity * 100)}% relevance to '{request.query}'"]
        if request.location and request.location.lower() in job.location.lower():
            reasons.append(f"Location match: {job.location}")

        scored_jobs.append(
            ScoredJobResponse(
                job=JobResponse.model_validate(job),
                similarity_score=round(similarity, 4),
                semantic_score=round(similarity, 4),
                match_reasons=reasons,
            )
        )

    return scored_jobs


def search_jobs_hybrid(
    db: Session,
    request: SemanticSearchRequest,
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> List[ScoredJobResponse]:
    """
    Hybrid Search combining:
    - Semantic similarity score from pgvector (weight: 0.6)
    - Keyword text occurrence score across title and description (weight: 0.4)
    """
    # 1. Fetch semantic candidates (fetch 2x top_k to allow re-ranking)
    semantic_request = SemanticSearchRequest(
        query=request.query,
        location=request.location,
        employment_type=request.employment_type,
        experience_level=request.experience_level,
        top_k=min(request.top_k * 2, 50),
    )
    semantic_results = search_jobs_semantic(db, semantic_request)
    
    # 2. Compute keyword match score for each candidate
    query_terms = [term.lower() for term in request.query.split() if len(term) > 2]
    
    hybrid_scored = []
    for item in semantic_results:
        job = item.job
        full_text = f"{job.title} {job.company} {job.description} {' '.join(job.required_skills)}".lower()

        # Keyword match ratio: proportion of query terms appearing in job text
        keyword_hits = sum(1 for term in query_terms if term in full_text)
        keyword_score = (keyword_hits / len(query_terms)) if query_terms else 0.5
        
        # Title bonus: if full term appears directly in title
        if any(term in job.title.lower() for term in query_terms):
            keyword_score = min(1.0, keyword_score + 0.25)

        # Weighted combined score
        combined_score = (semantic_weight * item.semantic_score) + (keyword_weight * keyword_score)

        # Build detailed reasons
        reasons = [f"Hybrid score: {int(combined_score * 100)}%"]
        if item.semantic_score >= 0.6:
            reasons.append(f"High conceptual relevance ({int(item.semantic_score * 100)}%)")
        if keyword_hits > 0:
            reasons.append(f"Matched {keyword_hits} search keyword(s)")

        hybrid_scored.append(
            ScoredJobResponse(
                job=job,
                similarity_score=round(combined_score, 4),
                semantic_score=item.semantic_score,
                keyword_score=round(keyword_score, 4),
                match_reasons=reasons,
            )
        )

    # Sort descending by combined score and take top_k
    hybrid_scored.sort(key=lambda x: x.similarity_score, reverse=True)
    return hybrid_scored[:request.top_k]
