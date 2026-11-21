# AI Career Agent

An intelligent, AI-powered career assistance platform built with **FastAPI**, **PostgreSQL + pgvector**, **Google Gemini**, **LangGraph** and **React**.

## Architecture
- **Frontend:** React + Vite + Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** PostgreSQL 16 + pgvector
- **LLM:** Google Gemini 1.5 Flash
- **Agent:** LangGraph
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node.js 20+

### 1. Clone and configure
```bash
git clone <repo-url>
cd ai-career-agent
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Start the database
```bash
docker compose up -d
```

### 3. Start the backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Open API docs
Visit http://localhost:8000/docs

## Development Phases
See the architecture document for the full 15-phase development roadmap.
