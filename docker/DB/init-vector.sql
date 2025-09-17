-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 문서 벡터 저장용 테이블
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    embedding vector(1536),  -- OpenAI 임베딩 차원
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 정보 벡터 저장용 테이블 (예시)
CREATE TABLE IF NOT EXISTS user_embeddings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    embedding vector(1536),
    embedding_type VARCHAR(50),  -- 'profile', 'preference' 등
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 벡터 유사도 검색을 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS documents_embedding_cosine_idx ON documents 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS documents_embedding_l2_idx ON documents 
USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS user_embeddings_cosine_idx ON user_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 메타데이터 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON documents USING GIN (metadata);
CREATE INDEX IF NOT EXISTS documents_created_at_idx ON documents (created_at);
CREATE INDEX IF NOT EXISTS user_embeddings_user_id_idx ON user_embeddings (user_id);
CREATE INDEX IF NOT EXISTS user_embeddings_type_idx ON user_embeddings (embedding_type);