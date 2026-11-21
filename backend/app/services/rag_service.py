"""
services/rag_service.py — Retrieval-Augmented Generation (RAG) Service

Implements:
1. Sliding window text chunking with overlap.
2. Knowledge base ingestion and pgvector vector storage.
3. Top-K context passage retrieval via cosine distance (<=>).
4. Grounded response generation using Gemini with source citations.
"""

import json
import os
from typing import List, Tuple, Dict, Any
from loguru import logger
import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.rag_chunk import RAGChunk
from app.schemas.rag import RAGSourceCitation, RAGQueryResponse
from app.services.embedding_service import embed_text, embed_batch


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Splits text into chunks of roughly `chunk_size` characters
    with `overlap` character buffer to avoid splitting concepts mid-sentence.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def seed_rag_knowledge_base(
    db: Session,
    file_path: str = "data/career_guidance_docs.json",
    force_reseed: bool = False,
) -> Tuple[int, int]:
    """
    Reads career guidance documents, chunks them, computes embeddings,
    and stores them in PostgreSQL rag_chunks table.
    Returns (created_chunks_count, total_docs_count).
    """
    # Locate file
    candidates = [
        file_path,
        os.path.join("..", file_path),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", file_path),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "career_guidance_docs.json")),
    ]
    target_path = None
    for p in candidates:
        if os.path.exists(p):
            target_path = p
            break

    if not target_path:
        logger.error(f"❌ Career guidance file not found at: {file_path}")
        return 0, 0

    with open(target_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    # Check if already seeded and not force
    existing_count = db.query(RAGChunk).count()
    if not force_reseed and existing_count >= len(docs):
        logger.info(f"RAG knowledge base already contains {existing_count} chunks.")
        return 0, len(docs)

    if force_reseed:
        db.query(RAGChunk).delete()
        db.commit()

    all_chunks_text = []
    all_chunks_meta = []

    for doc in docs:
        title = doc.get("title", "Career Guide")
        topic = doc.get("topic", "General")
        content = doc.get("content", "")
        
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        for i, c in enumerate(chunks):
            all_chunks_text.append(c)
            all_chunks_meta.append({
                "title": title,
                "topic": topic,
                "chunk_index": i,
            })

    logger.info(f"Generating embeddings for {len(all_chunks_text)} RAG knowledge chunks...")
    vectors = embed_batch(all_chunks_text)

    for text, meta, vec in zip(all_chunks_text, all_chunks_meta, vectors):
        chunk_obj = RAGChunk(
            source_title=meta["title"],
            source_type="guide",
            content=text,
            embedding=vec,
            metadata_fields={"topic": meta["topic"], "chunk_index": meta["chunk_index"]},
        )
        db.add(chunk_obj)

    db.commit()
    logger.info(f"✅ RAG knowledge base seeded with {len(all_chunks_text)} chunks.")
    return len(all_chunks_text), len(docs)


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    top_k: int = 3,
) -> List[Tuple[RAGChunk, float]]:
    """
    Retrieves top-K nearest document passages using pgvector cosine distance (<=>).
    Returns list of (RAGChunk, similarity_score).
    """
    # Ensure KB is seeded
    seed_rag_knowledge_base(db)

    query_vector = embed_text(query)
    distance_col = RAGChunk.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        select(RAGChunk, distance_col)
        .order_by("distance")
        .limit(top_k)
    )
    results = db.execute(stmt).all()

    output = []
    for chunk, distance in results:
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        output.append((chunk, round(similarity, 4)))
    return output


def answer_career_question_with_rag(
    db: Session,
    question: str,
    top_k: int = 3,
) -> RAGQueryResponse:
    """
    Full Grounded RAG Pipeline:
    1. Embeds candidate question.
    2. Retrieves top-K context chunks from pgvector.
    3. Prompts Gemini with strict instructions to answer ONLY using retrieved context.
    4. Attaches precise citations to the response.
    """
    retrieved = retrieve_relevant_chunks(db, question, top_k=top_k)
    
    # Build context string
    context_blocks = []
    citations = []
    for i, (chunk, sim) in enumerate(retrieved, 1):
        context_blocks.append(f"[Source {i}: {chunk.source_title}]\n{chunk.content}")
        citations.append(
            RAGSourceCitation(
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                snippet=chunk.content[:200] + "...",
                similarity_score=sim,
            )
        )

    context_str = "\n\n".join(context_blocks)

    system_instruction = (
        "You are an expert Career Coach and Technical Recruiter. "
        "Answer the candidate's question based PRIMARILY on the provided Context Sources below. "
        "Reference the source titles when offering advice. "
        "If the context does not contain enough information to answer fully, state what is covered in the documents "
        "and supplement with concise, accurate general engineering career best practices without hallucinating facts. "
        "Format your response with clear headings and bullet points."
    )

    prompt = (
        f"Context Sources:\n{context_str}\n\n"
        f"Candidate Question: {question}\n\n"
        "Please provide a grounded, practical answer with actionable steps:"
    )

    try:
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=system_instruction,
            generation_config={"temperature": 0.2},
        )
        res = model.generate_content(prompt)
        answer_text = res.text
    except Exception as e:
        logger.warning(f"Gemini RAG synthesis failed ({e}), constructing grounded summary.")
        answer_text = (
            f"Here is relevant guidance from our knowledge base regarding your question:\n\n"
            + "\n\n".join([f"**{c.source_title}**\n{c.snippet}" for c in citations])
        )

    return RAGQueryResponse(
        question=question,
        answer=answer_text,
        citations=citations,
        retrieved_chunk_count=len(retrieved),
    )
