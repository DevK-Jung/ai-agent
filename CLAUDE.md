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
[ LangGraph Router Workflow ]
    ├─ token_router edge (tiktoken 로컬 계산 · 토큰 초과 시 summarize 분기)
    ├─ summarize_node (gpt-4o-mini · messages 직접 교체 · RemoveMessage + SystemMessage)
    ├─ detect_agent (gpt-4o-mini · 인텐트 감지 · chat / meeting 분기)
    ├─ Chat Sub Agent
    │   ├─ classifier (gpt-4o-mini · FACT/SUMMARY/COMPARE/EVIDENCE)
    │   └─ generator (gpt-4o · RAG context · SSE streaming)
    ├─ Meeting Sub Agent
    │   ├─ transcribe_audio (WhisperX STT + 화자 분리)
    │   ├─ merge_transcript (화자별 발언 그룹화)
    │   └─ generate_minutes (gpt-4o · 구조화된 회의록)
    ├─ Vector Retriever (PostgreSQL + pgvector)
    └─ Document Processor (LlamaParser + 분리된 파서 시스템)
        ├─ PDF Parser (PyMuPDF + PyPDF2)
        ├─ DOCX Parser (python-docx)
        ├─ XLSX Parser (openpyxl)
        ├─ CSV Parser (multi-encoding)
        └─ DOC Parser (docx2txt/antiword)
    |
[ AI Infrastructure ]
    ├─ WhisperX Manager (스레드 안전 모델 캐싱)
    ├─ BGE-M3 Embedding Service
    └─ OpenAI LLM Services
    |
[ PostgreSQL + pgvector ] (Documents, Embeddings, Chat logs, Checkpointer)
```

## Core Concepts

### Multi-Agent Architecture
- **Router Workflow**: token_router edge → summarize/skip → detect_agent → chat/meeting 분기
- **Token Management**: `gpt4o.get_num_tokens_from_messages()` 로컬 계산 (API 비용 없음), 토큰 초과 시 messages 직접 교체 방식으로 요약
- **Chat Sub Agent**: Document-based Q&A with intelligent question classification (FACT, SUMMARY, COMPARE, EVIDENCE)
- **Meeting Sub Agent**: Audio-to-minutes pipeline with STT, speaker diarization, and AI summarization

### Token Management & Summarization
- **token_router edge**: START에서 토큰 수 체크, 초과 시 summarize_node로 분기
- **messages 직접 교체**: `RemoveMessage` + `SystemMessage(요약)` + kept messages를 한 번에 반환
- **토큰 예산 30% 보존**: 최신 메시지를 SUMMARIZE_MAX_TOKENS의 30% 이내로 유지
- **로컬 토큰 계산**: `gpt4o.get_num_tokens_from_messages()` 사용 (API 호출 없음)

### Audio Processing (WhisperX Integration)
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

### Router Workflow (router_workflow.py)
```
START
  → [token_router edge] ─ tiktoken 로컬 계산 (API 호출 없음)
      ├─ "summarize" → summarize_node → detect_agent
      │     (gpt-4o-mini 요약 · RemoveMessage + SystemMessage · 토큰 예산 30% 보존)
      └─ "skip"      → detect_agent
                           ↓ [select_agent edge]
                    ├─ "chat"    → Chat Sub Agent → END
                    └─ "meeting" → Meeting Sub Agent → END
```

### Chat Sub Agent (chat_workflow.py)
```
classifier (gpt-4o-mini · FACT/SUMMARY/COMPARE/EVIDENCE)
    → generator (gpt-4o · RAG context · SSE streaming)
```

### Meeting Sub Agent (meeting_workflow.py)
```
transcribe_audio (WhisperX STT + 화자 분리)
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
- **STT**: WhisperX (transcription + speaker diarization)
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

### WhisperX Model Management
- **Thread-safe Singleton Pattern**: WhisperXManager 클래스로 모델 관리
- **FastAPI Lifespan Integration**: 애플리케이션 시작 시 모델 사전 로드
- **Dynamic Model Loading**: 언어별 alignment 모델 동적 로드
- **Memory Optimization**: 긴 오디오용 배치 크기 자동 조정

### Prompt Management
- **프롬프트는 ChatPromptTemplate 사용**
- **노드 파일과 분리**: prompts/ 디렉토리에 별도 관리
- **프롬프트 상수는 prompts 모듈에 정의**

### Token Management
- **토큰 계산**: `gpt4o.get_num_tokens_from_messages()` 사용 (tiktoken 직접 사용 금지, API 비용 없음)
- **summarize_node**: `RemoveMessage` + `SystemMessage(요약)` + kept messages를 단일 dict로 반환
- **토큰 예산**: `SUMMARIZE_MAX_TOKENS * 0.3` 이내로 최신 메시지 유지

### Message and State Handling
- **isinstance로 메시지 타입 체크** (`type().__name__` 사용 금지)
- **State 직접 변경 금지**: 반환값으로만 상태 전달
- **messages 직접 교체**: 요약 시 삭제 + 요약 SystemMessage + kept messages를 한 번에 반환
- **RouterState**: `audio_file_path` 필드로 회의 에이전트에 오디오 파일 경로 전달

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

### Router Workflow (router_workflow.py)
```
START
  → [token_router edge]
      ├─ "summarize" → summarize_node → detect_agent
      └─ "skip"      → detect_agent
                           ↓ [select_agent edge]
                    ├─ "chat"    → Chat Sub Agent → END
                    └─ "meeting" → Meeting Sub Agent → END
```

### Chat Sub Agent (chat_workflow.py)
```
classifier (gpt-4o-mini · FACT/SUMMARY/COMPARE/EVIDENCE)
    → generator (gpt-4o · RAG context · SSE streaming)
```

### Meeting Sub Agent (meeting_workflow.py)
```
transcribe_audio (WhisperX)
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
│   │       ├── meeting.py           # Meeting API endpoints
│   │       └── users.py             # User API endpoints
│   ├── agents/                      # LangGraph agents and workflows
│   │   ├── constants.py             # WorkflowSteps, AgentTypes, StreamMessages
│   │   ├── state.py                 # RouterState, MeetingState
│   │   ├── core/
│   │   │   └── llm_provider.py      # gpt4o, gpt4o_mini 인스턴스
│   │   ├── edges/
│   │   │   └── router/
│   │   │       ├── token_router.py  # 토큰 초과 여부 분기 (START → summarize/skip)
│   │   │       └── agent_router.py  # agent_type 기반 서브 에이전트 선택
│   │   ├── nodes/
│   │   │   ├── router/
│   │   │   │   ├── summarize.py     # 요약 노드 (messages 직접 교체)
│   │   │   │   └── detect_agent.py  # 인텐트 감지 노드
│   │   │   ├── chat/                # Chat agent nodes
│   │   │   │   ├── classifier.py    # 질문 분류 (gpt-4o-mini)
│   │   │   │   ├── generator.py     # 답변 생성 (gpt-4o · SSE)
│   │   │   │   └── router.py        # 질문 유형 라우터
│   │   │   └── meeting/             # Meeting agent nodes
│   │   │       ├── transcribe_audio.py   # WhisperX STT + diarization
│   │   │       ├── merge_transcript.py    # Speaker grouping
│   │   │       └── generate_minutes.py   # AI meeting minutes
│   │   ├── prompts/                 # Prompt templates
│   │   │   ├── chat.py              # Chat prompts
│   │   │   ├── router.py            # 요약 · 에이전트 감지 프롬프트
│   │   │   └── meeting.py           # Meeting prompts
│   │   ├── workflows/               # Workflow definitions
│   │   │   ├── router_workflow.py   # 최상위 Router Workflow
│   │   │   ├── chat_workflow.py     # Chat Sub Agent 서브그래프
│   │   │   └── meeting_workflow.py  # Meeting Sub Agent 서브그래프
│   │   └── infra/                   # Agent infrastructure
│   │       └── checkpointer.py      # PostgreSQL checkpointer
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
│   │   │   └── whisperx_manager.py  # WhisperX model manager
│   │   ├── parsers/                 # Document parser system
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
├── notebook/
│   ├── workflow/
│   │   └── test_router_workflow.ipynb   # Router + Meeting 통합 테스트
│   ├── embedding/                   # 임베딩 관련 노트북
│   └── tools/                       # 툴 테스트 노트북
├── architecture/
│   └── route_architecture.html      # 아키텍처 시각화
├── docker/
│   └── docker-compose.infra.yml     # PostgreSQL with pgvector
├── data/                            # Data storage
│   ├── documents/                   # Original documents
│   ├── models/                      # AI model cache
│   └── test/                        # 테스트용 파일
├── pytest.ini                       # pytest configuration
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

### Phase 6: Meeting Agent Implementation ✅
1. **WhisperX Integration**: STT with speaker diarization
2. **Thread-safe Model Management**: FastAPI lifespan-based caching
3. **Long Audio Processing**: Chunked processing up to 2 hours
4. **Dynamic Performance Optimization**: Batch size adjustment
5. **AI Meeting Minutes**: Structured summary generation
6. **Meeting Sub Agent**: `create_meeting_subgraph()` via RouterState 통합

### Phase 7: Testing & Quality Assurance ✅
1. **Exception handler test coverage (16 test cases)**
2. **Mock-based testing for external services**
3. **Integration tests for Chat API**
4. **pytest configuration with proper Python path setup**

### Phase 8: Token Management & Router Workflow ✅
1. **token_router edge**: START에서 tiktoken 기반 토큰 수 체크 (API 비용 없음)
2. **summarize_node**: messages 직접 교체 방식 (RemoveMessage + SystemMessage)
3. **Router Workflow**: token_router → detect_agent → chat/meeting 분기 구조
4. **SUMMARIZE_PROMPT**: ChatPromptTemplate으로 분리 (`prompts/router.py`)
5. **Notebook Tests**: `notebook/workflow/test_router_workflow.ipynb`
6. **Architecture HTML**: `architecture/route_architecture.html` (아키텍처 시각화)

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
- **whisperx**: STT with speaker diarization
- **librosa**: Audio processing utilities
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
2. **Vector Search**: PostgreSQL + pgvector with BGE-M3 embeddings
3. **Router Workflow**: token_router edge → summarize/skip → detect_agent → chat/meeting
4. **Token Management**: `gpt4o.get_num_tokens_from_messages()` 로컬 계산, messages 직접 교체 방식 요약
5. **Meeting Agent (WhisperX)**:
   - Thread-safe model caching with FastAPI lifespan
   - Long audio processing (up to 2 hours, 10-minute chunks)
   - Dynamic batch sizing based on audio length
   - Speaker diarization and intelligent transcript merging
   - AI-powered meeting minutes generation
6. **Streaming API**: Real-time SSE responses with progress tracking
7. **Exception Handling**: Structured error responses with proper logging
8. **Configuration Management**: Complete .env-based settings with validation
9. **Testing Infrastructure**: pytest suite + `notebook/workflow/test_router_workflow.ipynb`

### Next Implementation Priority
1. **검색 결과 리랭킹**: 개선된 관련성 스코어링
2. **다국어 STT**: WhisperX 언어 지원 확장
3. **Redis 캐싱**: 성능 최적화
4. **사용자 인증**: 권한 관리