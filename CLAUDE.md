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
    ├─ Retriever (Milvus)
    ├─ Answer Generator (OpenAI)
    └─ Evidence Assembler
    |
[ PostgreSQL ]  (Question/Answer logs, Feedback)
[ Milvus ]     (Document Vector Store)
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
- **LLM**: OpenAI API
- **Vector DB**: Milvus
- **Metadata/Log DB**: PostgreSQL
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
# Start API server (development)
uvicorn app:app --host 0.0.0.0 --port 8080 --reload

# Run directly via main.py
python main.py
```

## Current Project Structure

```
/
├── app.py              # FastAPI application entry point
├── main.py             # Application runner with uvicorn
├── config/
│   └── config.py       # Configuration settings
├── controller/
│   ├── __init__.py
│   └── users.py        # Basic user endpoints (placeholder)
└── pyproject.toml      # Project dependencies and metadata
```

## Implementation Phases

### Phase 1: Basic RAG Foundation
1. Document collection and preprocessing
2. Chunking strategy implementation
3. Embedding generation
4. Milvus vector storage
5. Basic Retrieval + Answer generation API

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

## Key Dependencies

- **fastapi**: Web framework for API endpoints
- **langchain**: LLM framework and integrations
- **langgraph**: Graph-based workflow orchestration
- **uvicorn**: ASGI server for FastAPI

## Development Notes

- Current implementation is minimal FastAPI setup
- Controller structure follows modular pattern
- Configuration is centralized in config/config.py
- Server runs on port 8080 by default

## Next Steps for Implementation

1. Add required dependencies (OpenAI, Milvus, PostgreSQL clients)
2. Implement LangGraph nodes for question processing
3. Set up vector storage and document management
4. Create RAG pipeline with agent-based routing
5. Implement explainable answer formatting