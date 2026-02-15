# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AI Development Best Practices

This project follows proven AI-assisted development principles for optimal code quality and efficiency:

### Core Development Principles

#### 1. Think Before Coding
- **Explicit Assumptions**: Always state assumptions about requirements and context
- **Surface Ambiguity**: When requirements are unclear, present multiple interpretations and ask for clarification
- **Clarifying Questions**: Ask specific questions before implementation to avoid rework
- **Push Back on Complexity**: Question overly complex approaches and suggest simpler alternatives

#### 2. Simplicity First
- **Minimum Viable Code**: Write only the code necessary to solve the immediate problem
- **No Speculative Features**: Avoid implementing features that "might be useful later"
- **Reject Abstractions**: Unless abstraction clearly reduces complexity, prefer concrete solutions
- **Concise Solutions**: Aim for the most straightforward implementation that works

#### 3. Surgical Changes
- **Targeted Modifications**: Only change code directly related to the current task
- **Preserve Style**: Match existing code patterns, naming conventions, and structure
- **Minimal Cleanup**: Remove only code that becomes unused by your changes
- **Avoid Refactoring**: Don't refactor unrelated code unless explicitly requested

#### 4. Goal-Driven Execution
- **Verifiable Goals**: Transform vague tasks into specific, testable objectives
- **Success Criteria**: Define explicit criteria for when a task is complete
- **Test-First**: Write tests or verification steps before implementing features
- **Verification Loops**: Continuously verify that changes meet the stated goals

### Implementation Guidelines

#### Before Starting Any Task:
1. **Understand Context**: Read existing code and documentation thoroughly
2. **State Assumptions**: Explicitly mention what you understand about the requirements
3. **Ask Questions**: If anything is unclear, ask specific clarifying questions
4. **Define Success**: Establish clear criteria for what "done" looks like

#### During Implementation:
1. **Minimal Changes**: Make the smallest possible change to achieve the goal
2. **Follow Patterns**: Use existing code patterns and conventions
3. **Test Incrementally**: Verify each small change works before proceeding
4. **Stay Focused**: Resist the urge to fix unrelated issues

#### Code Quality Indicators:
✅ **Good Signs:**
- Small, focused changes
- Changes directly address the stated problem
- New code follows existing patterns
- Clear reasoning for implementation choices

❌ **Warning Signs:**
- Large, sweeping changes
- Refactoring unrelated code
- Adding "just in case" features
- Complex solutions for simple problems

## Project Overview

This is an Agent-based Explainable RAG (Retrieval-Augmented Generation) system that goes beyond simple RAG demos to implement enterprise-level architecture with questioning intent understanding, retrieval strategy selection, and evidence-based answers.

## Architecture

```
[ Client ]
    |
[ FastAPI + Exception Handlers ]
    |
[ LangGraph Orchestrator with SSE Streaming ]
    ├─ Question Classifier Agent (gpt-4o-mini)
    ├─ Answer Generator Agent (gpt-4o)  
    ├─ Vector Retriever (PostgreSQL + pgvector)
    ├─ Document Processor (LlamaParser + BGE-M3)
    └─ Real-time Status Tracking
    |
[ PostgreSQL + pgvector ]  (Documents, Embeddings, Chat logs)
```

## Core Concepts

- **Question Classification**: Agents interpret and classify user questions (FACT, SUMMARY, COMPARE, EVIDENCE)
- **Streaming Responses**: Real-time SSE streaming with workflow progress tracking
- **Document Processing**: LlamaParser for high-quality PDF/Office document conversion
- **Exception Handling**: Comprehensive error handling with structured responses
- **LangGraph Structure**: Clear node-based reasoning flow with constants management

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
├── main.py                           # FastAPI app + uvicorn runner (single entry point)
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── chat.py              # Chat API endpoints (with SSE streaming)
│   │       ├── documents.py         # Document upload/management API
│   │       ├── search.py            # Search API endpoints
│   │       └── users.py             # User API endpoints
│   ├── agents/                      # LangGraph agents and workflows
│   │   ├── constants.py             # Workflow steps and message constants
│   │   ├── nodes/                   # Individual agent nodes
│   │   ├── prompts/                 # Prompt templates
│   │   ├── workflows/               # Workflow definitions
│   │   │   └── chat_workflow.py     # Main chat workflow with streaming
│   │   └── state.py                 # State management
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── document.py              # Document and DocumentChunk models
│   ├── services/                    # Business logic layer
│   │   ├── document_service.py      # Document processing service
│   │   └── search_service.py        # Search service
│   ├── schemas/                     # Pydantic models for API
│   │   ├── chat.py                  # Chat request/response schemas
│   │   ├── document.py              # Document schemas
│   │   ├── errors.py                # Error response schemas
│   │   └── search.py                # Search schemas
│   ├── infra/                       # Infrastructure services
│   │   ├── ai/                      # AI services (embeddings)
│   │   ├── llama_parser.py          # LlamaParser integration
│   │   └── storage/                 # File storage services
│   ├── core/                        # Core configuration
│   │   ├── config.py                # Configuration with pydantic-settings
│   │   ├── exceptions.py            # Custom exception classes
│   │   ├── exception_handlers.py    # FastAPI exception handlers
│   │   └── logging.py               # Logging configuration
│   ├── db/                          # Database connections and utilities
│   │   ├── __init__.py
│   │   └── database.py              # Async SQLAlchemy setup
│   └── utils/                       # Utility functions
├── tests/                           # Test files
│   ├── test_exception_handlers.py   # Comprehensive exception handler tests
│   └── ...                         # Other test files
├── docker/
│   └── docker-compose.infra.yml     # PostgreSQL with pgvector
├── data/                            # Data storage
│   ├── documents/                   # Original documents
│   ├── models/                      # AI model cache
│   └── processed/                   # Processed data
├── scripts/                         # Utility scripts
├── notebook/                        # Jupyter notebooks for development
├── pytest.ini                      # pytest configuration
├── .env                             # Environment variables
└── pyproject.toml                   # Project dependencies
```

## Implementation Phases

### Phase 1: Core Infrastructure ✅
1. PostgreSQL + pgvector setup with Docker
2. SQLAlchemy async ORM models (Document, DocumentChunk)
3. Database connection and initialization
4. BGE-M3 embedding model preparation
5. **FastAPI exception handlers with structured error responses**
6. **Comprehensive test suite with pytest configuration**

### Phase 2: Document Processing ✅
1. **LlamaParser integration for high-quality document conversion**
2. Document upload and processing pipeline
3. Multiple file format support (PDF, Excel, PowerPoint, Word)
4. Embedding generation and vector storage

### Phase 3: LangGraph Workflow ✅
1. LangGraph project structure design
2. Question Classifier Node implementation (gpt-4o-mini)
3. Answer Generator Node implementation (gpt-4o)
4. **Real-time SSE streaming with workflow progress tracking**
5. **Constants and message management for maintainability**
6. State management between nodes

### Phase 4: Search & Retrieval ✅
1. Semantic search implementation
2. Hybrid search (keyword + semantic)
3. Search statistics and monitoring
4. Multiple retrieval strategies

### Phase 5: API Enhancement ✅
1. **Streaming chat API with Server-Sent Events**
2. Document management API
3. Search API endpoints
4. Health check and monitoring endpoints

### Phase 6: Testing & Quality Assurance ✅
1. **Exception handler test coverage (16 test cases)**
2. **Mock-based testing for external services**
3. **Integration tests for Chat API**
4. **pytest configuration with proper Python path setup**

## Configuration

- Environment variables are managed in `.env` file
- Configuration class uses `pydantic-settings` for validation
- Default server port: 8000 (configurable via PORT environment variable)
- OpenAI API key required in OPENAI_API_KEY environment variable

## Key Dependencies

### Core Framework
- **fastapi**: Web framework for API endpoints
- **uvicorn**: ASGI server for FastAPI
- **pydantic-settings**: Configuration management
- **python-dotenv**: Environment variable loading

### AI & ML
- **langchain & langchain-openai**: LLM framework and OpenAI integration
- **langgraph**: Graph-based workflow orchestration  
- **sentence-transformers**: BGE-M3 embedding model
- **torch**: PyTorch for model inference
- **llama-cloud**: LlamaParser for document processing

### Database & Storage
- **sqlalchemy**: ORM for database operations
- **asyncpg**: PostgreSQL async driver
- **pgvector**: PostgreSQL vector extension Python interface

### Real-time Features
- **sse-starlette**: Server-Sent Events for streaming responses

### Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **httpx**: HTTP client for testing

### Development
- **dependency-groups**: Modern Python dependency management

## Development Notes

- Single `main.py` entry point follows FastAPI best practices
- Modular app structure separates concerns (API, agents, services, etc.)
- Configuration centralized in `app/core/config.py` with environment validation
- Server runs on port 8000 by default (configurable)
- Uses structured directory layout for enterprise-level development
- **Comprehensive exception handling with structured error responses**
- **Real-time streaming capabilities with SSE**
- **Test-driven development with pytest configuration**

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_exception_handlers.py

# Run with verbose output
python -m pytest -v

# Run tests with coverage
python -m pytest --cov=app tests/
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Exception Handler Tests**: Comprehensive error handling verification
- **Mock Tests**: External service mocking

## Current Features

### Completed ✅
1. **Document Processing**: LlamaParser integration for high-quality conversion
2. **Vector Search**: PostgreSQL + pgvector with BGE-M3 embeddings
3. **LangGraph Workflow**: Question classification and answer generation
4. **Streaming API**: Real-time SSE responses with progress tracking
5. **Exception Handling**: Structured error responses with proper logging
6. **Testing Infrastructure**: Comprehensive test suite with proper configuration

### Next Implementation Priority
1. Search result re-ranking system
2. User feedback collection and analysis
3. Answer quality evaluation metrics
4. Redis caching layer
5. Kubernetes deployment configuration