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
[ FastAPI + Exception Handlers + SSE Streaming ]
    |
[ LangGraph Orchestrator with Real-time Progress Tracking ]
    ├─ Router Agent (공통 처리: 대화 이력, 토큰 체크, 요약, DB 저장)
    ├─ Chat Sub Agent (질문 분류 + 답변 생성)
    │   ├─ Question Classifier Agent (gpt-4o-mini)
    │   └─ Answer Generator Agent (gpt-4o)
    ├─ Meeting Sub Agent (STT + 화자 분리 + 회의록 생성) ⭐ NEW
    │   ├─ WhisperX Audio Transcription (긴 오디오 청킹 처리)
    │   ├─ Speaker Diarization (pyannote)
    │   └─ Meeting Minutes Generator (gpt-4o)
    ├─ Vector Retriever (PostgreSQL + pgvector)
    └─ Document Processor (LlamaParser + 분리된 파서 시스템)
        ├─ PDF Parser (PyMuPDF + PyPDF2)
        ├─ DOCX Parser (python-docx)
        ├─ XLSX Parser (openpyxl)
        ├─ CSV Parser (multi-encoding)
        └─ DOC Parser (docx2txt/antiword)
    |
[ AI Infrastructure ]
    ├─ WhisperX Manager (스레드 안전 모델 캐싱) ⭐ NEW
    ├─ BGE-M3 Embedding Service
    └─ OpenAI LLM Services
    |
[ PostgreSQL + pgvector ] (Documents, Embeddings, Chat logs, Checkpointer)
```

## Core Concepts

### Multi-Agent Architecture
- **Router Agent**: Common processing logic (conversation history, token management, summarization, DB operations)
- **Chat Sub Agent**: Document-based Q&A with intelligent question classification (FACT, SUMMARY, COMPARE, EVIDENCE)
- **Meeting Sub Agent**: Audio-to-minutes pipeline with STT, speaker diarization, and AI summarization ⭐ NEW

### Audio Processing (WhisperX Integration) ⭐ NEW
- **Thread-safe Model Management**: FastAPI lifespan-based model caching with WhisperXManager
- **Long Audio Support**: Chunked processing for files up to 2 hours (10-minute chunks)
- **Dynamic Batch Sizing**: Automatic batch size adjustment based on audio length
- **Speaker Diarization**: pyannote-based speaker identification and separation
- **Intelligent Transcription**: Language detection with alignment optimization

### Document & Content Processing
- **LlamaParser Integration**: High-quality document conversion for PDF/Excel/PowerPoint/Word
- **Separated Parser System**: Factory pattern with specialized parsers for optimal file handling
  - Support for PDF, DOC, DOCX, XLSX, CSV formats
  - Multi-encoding support for international documents (CP949, EUC-KR, UTF-8)
  - Fallback mechanisms for robust parsing
- **BGE-M3 Local Embeddings**: High-quality multilingual embeddings

### Real-time & Streaming
- **SSE Streaming**: Real-time responses with workflow progress tracking
- **Live Status Updates**: Step-by-step processing status for long-running operations
- **Async Processing**: Non-blocking operations with proper error handling

### Infrastructure & Quality
- **Exception Handling**: Comprehensive error handling with structured responses
- **LangGraph Structure**: Clear node-based reasoning flow with constants management
- **Configuration Management**: Complete .env-based configuration with validation
- **Thread Safety**: Proper concurrent processing with model caching

## Current Multi-Agent Architecture (Implemented) ✅

다중 에이전트 아키텍처로 성공적으로 리팩토링 완료:
- **Router Agent**: 공통 처리 (대화 이력, 토큰 체크, 요약, DB 저장)
- **Chat Sub Agent**: 질문 분류 + 답변 생성
- **Meeting Sub Agent**: WhisperX STT + pyannote 화자 분리 + AI 회의록 생성 ✅

### Meeting Workflow (meeting_workflow.py) ⭐ NEW
```
audio_upload
    → transcribe_audio (WhisperX STT + 화자 분리)
        ├─ 긴 오디오 감지 (30분+ → 10분 청킹)
        ├─ 동적 배치 크기 조정
        └─ 스레드 안전 모델 캐싱
    → merge_transcript (화자별 발언 그룹화)
    → generate_minutes (구조화된 회의록 생성)
```

## Technology Stack

### Core Framework
- **Language**: Python 3.13+
- **API Server**: FastAPI with async support
- **LLM Orchestration**: LangGraph
- **Real-time**: Server-Sent Events (SSE) streaming
- **Container**: Docker Compose

### AI & ML
- **LLM**: OpenAI GPT-4o (답변/회의록), GPT-4o-mini (분류)
- **STT**: WhisperX (transcription + speaker diarization) ⭐ NEW
- **Embedding**: BGE-M3 (HuggingFace local inference)
- **Document Processing**: LlamaParser + custom parser factory

### Database & Storage
- **Database**: PostgreSQL with async SQLAlchemy
- **Vector Database**: PostgreSQL with pgvector extension
- **State Management**: PostgreSQL-based checkpointer
- **File Storage**: Structured local filesystem

## Code Conventions

**IMPORTANT**: All code must follow these conventions exactly to ensure consistency and maintainability.

### LLM and Chain Management
- **LLM 인스턴스는 모듈 레벨에서 생성** (함수 내부 생성 금지)
- **LCEL 체인으로 구성**: `prompt | llm | parser` 패턴 사용
- **단순 텍스트 반환은 StrOutputParser 사용**

### WhisperX Model Management ⭐ NEW
- **Thread-safe Singleton Pattern**: WhisperXManager 클래스로 모델 관리
- **FastAPI Lifespan Integration**: 애플리케이션 시작 시 모델 사전 로드
- **Dynamic Model Loading**: 언어별 alignment 모델 동적 로드
- **Memory Optimization**: 긴 오디오용 배치 크기 자동 조정

### Prompt Management
- **프롬프트는 ChatPromptTemplate 사용**
- **노드 파일과 분리**: prompts/ 디렉토리에 별도 관리
- **프롬프트 상수는 prompts 모듈에 정의**

### Message and State Handling
- **isinstance로 메시지 타입 체크** (`type().__name__` 사용 금지)
- **State 직접 변경 금지**: 반환값으로만 상태 전달
- **RemoveMessage 사용 시**: `messages[-2:]`는 반환값에 포함하지 않음

### Database Operations
- **DB 세션 로직은 헬퍼 함수로 분리**
- **async/await 패턴 일관성 유지**

### Error Handling
- **구조화된 에러 응답 사용**
- **예외 상황에서 기본값 반환**
- **Logging with Context**: exc_info=True로 상세 오류 정보 로깅
- **Graceful Degradation**: 모델 로드 실패 시 우아한 실패 처리

### Code Quality
- **타입 힌트 사용**
- **명확한 함수명과 변수명**
- **단일 책임 원칙 준수**

## Current Workflows

### Chat Workflow (chat_workflow.py)
```
need_prev_conversation (is_new_session 기반)
    → load_history_from_db 또는 check_token
    → summarize_conversation (8000토큰 초과시)
    → classify_question (FACT, SUMMARY, COMPARE, EVIDENCE)
    → generate_answer (카테고리별 맞춤 프롬프트)
    → save_message_to_db
```

### Meeting Workflow (meeting_workflow.py) ⭐ NEW
```
audio_upload
    → transcribe_audio (WhisperX)
        ├─ 오디오 길이 체크 (최대 2시간)
        ├─ 긴 오디오 시 10분 단위 청킹
        ├─ 동적 배치 크기 (8-16)
        ├─ 언어 감지 및 정렬
        └─ 화자 분리 (pyannote)
    → merge_transcript (화자별 발언 그룹화)
    → generate_minutes (AI 기반 구조화된 회의록)
```

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

# Start API server (runs on port 8888 by default, configurable via PORT)
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
│   │       ├── meeting.py           # Meeting API endpoints ⭐ NEW
│   │       └── users.py             # User API endpoints
│   ├── agents/                      # LangGraph agents and workflows
│   │   ├── constants.py             # Workflow steps and message constants
│   │   ├── nodes/                   # Individual agent nodes
│   │   │   ├── chat/                # Chat agent nodes
│   │   │   └── meeting/             # Meeting agent nodes ⭐ NEW
│   │   │       ├── transcribe_audio.py   # WhisperX STT + diarization
│   │   │       ├── merge_transcript.py    # Speaker grouping
│   │   │       └── generate_minutes.py   # AI meeting minutes
│   │   ├── prompts/                 # Prompt templates
│   │   │   ├── chat.py              # Chat prompts
│   │   │   └── meeting.py           # Meeting prompts ⭐ NEW
│   │   ├── workflows/               # Workflow definitions
│   │   │   ├── chat_workflow.py     # Chat workflow with streaming
│   │   │   └── meeting_workflow.py  # Meeting workflow ⭐ NEW
│   │   ├── infra/                   # Agent infrastructure
│   │   └── state.py                 # State management (ChatState, MeetingState)
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
│   │   ├── ai/                      # AI services
│   │   │   ├── embedding_service.py # BGE-M3 embeddings
│   │   │   └── whisperx_manager.py  # WhisperX model manager ⭐ NEW
│   │   ├── parsers/                 # Document parser system ⭐ NEW
│   │   │   ├── __init__.py          # ParserFactory export
│   │   │   ├── factory.py           # Parser factory with MIME type mapping
│   │   │   ├── base.py              # BaseParser abstract class
│   │   │   ├── models.py            # ParsedContent, Table, Image models
│   │   │   ├── pdf_parser.py        # PDF parser (PyMuPDF + PyPDF2)
│   │   │   ├── docx_parser.py       # DOCX parser (python-docx)
│   │   │   ├── xlsx_parser.py       # XLSX parser (openpyxl)
│   │   │   ├── csv_parser.py        # CSV parser (multi-encoding)
│   │   │   └── doc_parser.py        # DOC parser (docx2txt/antiword)
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

## Implementation Status

### Phase 1: Core Infrastructure ✅
1. PostgreSQL + pgvector setup with Docker
2. SQLAlchemy async ORM models (Document, DocumentChunk)
3. Database connection and initialization
4. BGE-M3 embedding model preparation
5. **FastAPI exception handlers with structured error responses**
6. **Comprehensive test suite with pytest configuration**

### Phase 2: Document Processing ✅
1. **LlamaParser integration for high-quality document conversion**
2. **Separated parser system implementation** - Factory pattern with specialized parsers
3. Multiple file format support (PDF, DOC, DOCX, XLSX, CSV)
4. Multi-encoding support for international documents (CP949, EUC-KR, UTF-8)
5. Document upload and processing pipeline
6. Embedding generation and vector storage

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

### Phase 6: Meeting Agent Implementation ✅ ⭐ NEW
1. **WhisperX Integration**: STT with speaker diarization
2. **Thread-safe Model Management**: FastAPI lifespan-based caching
3. **Long Audio Processing**: Chunked processing up to 2 hours
4. **Dynamic Performance Optimization**: Batch size adjustment
5. **AI Meeting Minutes**: Structured summary generation
6. **Real-time Progress Tracking**: Workflow status monitoring

### Phase 7: Testing & Quality Assurance ✅
1. **Exception handler test coverage (16 test cases)**
2. **Mock-based testing for external services**
3. **Integration tests for Chat API**
4. **pytest configuration with proper Python path setup**

## Configuration

- Environment variables are managed in `.env` file (copy from `.env.example`)
- Configuration class uses `pydantic-settings` for validation
- Default server port: 8888 (configurable via PORT environment variable)
- Required API keys: OPENAI_API_KEY, LLAMA_CLOUD_API_KEY, HF_TOKEN
- WhisperX settings: model size, device, language, batch size, audio length limits
- Complete configuration reference in `.env.example`

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
- **whisperx**: STT with speaker diarization ⭐ NEW
- **librosa**: Audio processing utilities ⭐ NEW
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
- Server runs on port 8888 by default (configurable via PORT)
- Uses structured directory layout for enterprise-level development
- Multi-agent architecture with clear separation of concerns
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
1. **Document Processing**: 
   - LlamaParser integration for high-quality conversion
   - Separated parser system with Factory pattern (PDF, DOC, DOCX, XLSX, CSV)
   - Multi-encoding support for international documents
   - Repository pattern implementation with dependency injection
2. **Vector Search**: PostgreSQL + pgvector with BGE-M3 embeddings
3. **Multi-Agent Architecture**: Router + Chat + Meeting agents
4. **Meeting Agent (WhisperX)**: ⭐ NEW
   - Thread-safe model caching with FastAPI lifespan
   - Long audio processing (up to 2 hours, 10-minute chunks)
   - Dynamic batch sizing based on audio length
   - Speaker diarization and intelligent transcript merging
   - AI-powered meeting minutes generation
5. **Streaming API**: Real-time SSE responses with progress tracking
6. **Exception Handling**: Structured error responses with proper logging
7. **Configuration Management**: Complete .env-based settings with validation
8. **Testing Infrastructure**: Comprehensive test suite with proper configuration

### Next Implementation Priority
1. **STT Progress Monitoring**: Real-time progress updates for long audio processing
2. **Multi-language STT**: Extended language support for WhisperX
3. **Meeting Template Customization**: Configurable meeting minutes formats
4. **Search Result Re-ranking**: Improved relevance scoring
5. **Redis Caching**: Performance optimization
6. **User Feedback System**: Quality assessment and improvement