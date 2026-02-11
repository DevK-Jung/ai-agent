# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Agent-based Explainable RAG (Retrieval-Augmented Generation) system that goes beyond simple RAG demos to implement enterprise-level architecture with questioning intent understanding, retrieval strategy selection, and evidence-based answers.

## Architecture

```
[ Client ]
    |
[ FastAPI ]
    |
[ LangGraph Orchestrator ]
    ├─ Question Classifier Agent
    ├─ Retrieval Strategy Selector Agent
    ├─ Vector Retriever (PostgreSQL + pgvector)
    ├─ Answer Generator (BGE-M3)
    └─ Evidence Assembler
    |
[ PostgreSQL + pgvector ]  (Documents, Embeddings, Chat logs)
```

## Core Concepts

- **Question Classification**: Agents interpret and classify user questions (FACT, SUMMARY, COMPARE, EVIDENCE)
- **Dynamic Retrieval Strategy**: Selects appropriate retrieval strategy based on question type
- **Explainable Answers**: Provides evidence documents alongside answers
- **LangGraph Structure**: Clear node-based reasoning flow

## Technology Stack

- **Language**: Python
- **API Server**: FastAPI
- **LLM Orchestration**: LangGraph
- **Embedding Model**: BGE-M3 (HuggingFace)
- **Vector Database**: PostgreSQL with pgvector extension
- **Database**: PostgreSQL with async SQLAlchemy
- **Container**: Docker

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Run development server
python main.py
```

### Running Services
```bash
# Start PostgreSQL with pgvector
docker compose --env-file .env -f docker/docker-compose.infra.yml up -d

# Start API server (runs on port 8888 by default)
python main.py

# Access API documentation
# http://localhost:8888/docs (Swagger UI)
# http://localhost:8888/redoc (ReDoc)
```

## Current Project Structure

```
/
├── main.py                    # FastAPI app + uvicorn runner (single entry point)
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── chat.py        # Chat API endpoints
│   │       └── users.py       # User API endpoints
│   ├── agents/                # LangGraph agents and workflows
│   │   ├── nodes/            # Individual agent nodes
│   │   └── workflows/        # Workflow definitions
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── document.py       # Document and DocumentChunk models
│   ├── services/             # Business logic layer
│   ├── schemas/              # Pydantic models for API
│   ├── core/
│   │   └── config.py         # Configuration with pydantic-settings
│   ├── db/                   # Database connections and utilities
│   │   ├── __init__.py
│   │   └── database.py       # Async SQLAlchemy setup
│   └── utils/                # Utility functions
├── docker/
│   └── docker-compose.infra.yml  # PostgreSQL with pgvector
├── data/                     # Data storage
│   ├── documents/            # Original documents
│   └── processed/            # Processed data
├── scripts/                  # Utility scripts
├── tests/                    # Test files
├── docker/                   # Docker configuration
├── notebook/                 # Jupyter notebooks for development
├── .env                      # Environment variables
└── pyproject.toml           # Project dependencies
```

## Implementation Phases

### Phase 1: Database & Infrastructure ✅
1. PostgreSQL + pgvector setup with Docker
2. SQLAlchemy async ORM models (Document, DocumentChunk)
3. Database connection and initialization
4. BGE-M3 embedding model preparation

### Phase 2: LangGraph Integration
1. LangGraph project structure design
2. Question Classifier Node implementation
3. Graph flow: classify → retrieve → answer
4. State management between nodes

### Phase 3: Advanced Retrieval
1. Retrieval Strategy Selector Node
2. Multiple retrieval strategies (Semantic, Keyword+Metadata, Hybrid)
3. Evidence scoring logic

### Phase 4: Service Enhancement
1. Structured Answer + Evidence response format
2. Document viewing API
3. Question/Answer logging
4. Docker Compose configuration

### Phase 5: Advanced Features (Optional)
1. User feedback collection API
2. Retrieval weight adjustment logic
3. RAG evaluation and monitoring

## Configuration

- Environment variables are managed in `.env` file
- Configuration class uses `pydantic-settings` for validation
- Default server port: 8000 (configurable via PORT environment variable)
- OpenAI API key required in OPENAI_API_KEY environment variable

## Key Dependencies

- **fastapi**: Web framework for API endpoints
- **langchain & langchain-openai**: LLM framework and OpenAI integration
- **langgraph**: Graph-based workflow orchestration  
- **uvicorn**: ASGI server for FastAPI
- **pydantic-settings**: Configuration management
- **python-dotenv**: Environment variable loading
- **sqlalchemy**: ORM for database operations
- **asyncpg**: PostgreSQL async driver
- **pgvector**: PostgreSQL vector extension Python interface
- **sentence-transformers**: BGE-M3 embedding model
- **torch**: PyTorch for model inference

## Development Notes

- Single `main.py` entry point follows FastAPI best practices
- Modular app structure separates concerns (API, agents, services, etc.)
- Configuration centralized in `app/core/config.py` with environment validation
- Server runs on port 8000 by default (configurable)
- Uses structured directory layout for enterprise-level development

## Next Steps for Implementation

1. Add RAG-specific dependencies (Milvus, PostgreSQL, text processing)
2. Implement LangGraph nodes for question processing workflow
3. Set up vector storage and document management services
4. Create agent-based routing and retrieval strategies
5. Implement explainable answer formatting with evidence