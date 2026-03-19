-- pgvector 확장
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_bigm 확장 (GIN 기반 한국어/다국어 LIKE 검색 가속)
CREATE EXTENSION IF NOT EXISTS pg_bigm;
