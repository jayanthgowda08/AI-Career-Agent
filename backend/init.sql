-- This script runs automatically when the PostgreSQL container starts for the first time.
-- It enables the pgvector extension needed for storing and searching embeddings.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- for fuzzy/keyword search
CREATE EXTENSION IF NOT EXISTS unaccent; -- for accent-insensitive search
