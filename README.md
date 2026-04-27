# AI Agent RAG System

Agent-based Explainable RAG (Retrieval-Augmented Generation) System - 엔터프라이즈급 다중 에이전트 AI 시스템입니다.

## 프로젝트 개요

단순한 RAG 데모를 넘어선 엔터프라이즈 수준의 아키텍처를 구현하는 프로젝트입니다. 질문 의도 이해, 검색 전략 선택, 증거 기반 답변 생성을 통한 설명 가능한 AI 시스템을 제공합니다.

**핵심 특징:**
- 다중 에이전트 아키텍처: Supervisor 패턴 기반 동적 에이전트 라우팅
- CRAG(Corrective RAG): 내부 검색 → 관련성 평가 → 웹 검색 폴백 전략
- 고급 문서 처리: LlamaParser + 분리된 파서 시스템으로 고품질 텍스트 추출
- 회의록 자동 생성: WhisperX STT + 화자 분리 + AI 회의록 작성
- 실시간 스트리밍: SSE 기반 실시간 응답 및 진행 상황 추적
- 외부 도구 통합: Gmail, Arxiv, DuckDuckGo 검색 Tool 연동

## 아키텍처

```
[ Client ]
    |
[ FastAPI + Exception Handlers + SSE Streaming ]
    |
[ LangGraph Router Workflow — Supervisor 패턴 ]
    ├─ supervisor_node (gpt-4o · 토큰 체크 · 다음 에이전트 결정)
    │     ├─ → summarize_conversations (토큰 초과 시 자동 요약)
    │     ├─ → chat_agent    (문서 기반 Q&A)
    │     ├─ → rag_agent     (CRAG — Corrective RAG)
    │     ├─ → meeting_agent (회의록 생성)
    │     └─ → final_response_agent (최종 응답 정리)
    |
[ Sub-Agents ]
    ├─ Chat Sub Agent (chat_workflow.py)
    │   ├─ classifier (gpt-4o-mini · FACT/SUMMARY/COMPARE/EVIDENCE)
    │   └─ generator  (gpt-4o · RAG context · SSE streaming)
    ├─ RAG Sub Agent — CRAG (rag_workflow.py)
    │   ├─ rewrite         (쿼리 재정의)
    │   ├─ internal_search (pgvector 검색)
    │   ├─ internal_relevance_edge (관련성 평가 → relevant/rewrite/web_search)
    │   ├─ web_search      (DuckDuckGo 폴백)
    │   ├─ web_relevance_edge (관련성 평가 → relevant/irrelevant)
    │   ├─ answer          (최종 답변 생성)
    │   └─ fallback        (관련 정보 없음 처리)
    └─ Meeting Sub Agent (meeting_workflow.py)
        ├─ transcribe_audio (WhisperX STT + 화자 분리)
        ├─ merge_transcript (화자별 발언 그룹화)
        └─ generate_minutes (gpt-4o · 구조화된 회의록)
    |
[ Tools ]
    ├─ internal_search (PostgreSQL + pgvector)
    ├─ duckduckgo      (웹 검색)
    ├─ arxiv           (논문 검색)
    └─ gmail           (이메일 연동)
    |
[ AI Infrastructure ]
    ├─ WhisperX Manager (스레드 안전 모델 캐싱)
    ├─ BGE-M3 Embedding Service
    └─ OpenAI LLM Services
    |
[ Database Layer ]
    ├─ PostgreSQL (문서, 대화 이력, 체크포인터)
    └─ pgvector (벡터 저장소)
```

### 구현된 워크플로우

#### Router Workflow — Supervisor 패턴 (router_workflow.py)
```
START → supervisor
  supervisor
    ├─ 토큰 초과 감지 → summarize_conversations → supervisor
    ├─ → chat_agent    → supervisor
    ├─ → rag_agent     → supervisor
    ├─ → meeting_agent → supervisor
    └─ FINISH → final_response_agent → END
```

#### RAG Sub Agent — CRAG (rag_workflow.py)
```
START → rewrite → internal_search
  internal_search → [internal_relevance_edge]
      ├─ relevant   → answer → END
      ├─ rewrite    → rewrite (retry)
      └─ web_search → web_search → [web_relevance_edge]
                          ├─ relevant   → answer → END
                          └─ irrelevant → fallback → END
```

#### Chat Sub Agent (chat_workflow.py)
```
classifier (gpt-4o-mini · FACT/SUMMARY/COMPARE/EVIDENCE)
    → generator (gpt-4o · RAG context · SSE streaming)
```

#### Meeting Sub Agent (meeting_workflow.py)
```
transcribe_audio (WhisperX STT + 화자 분리)
    → merge_transcript (화자별 발언 그룹화)
    → generate_minutes (gpt-4o · 구조화된 회의록)
```

#### Document Processing
1. **Multi-format Upload**: PDF, DOC, DOCX, XLSX, CSV 지원
2. **High-quality Parsing**: LlamaParser + 분리된 파서 시스템
3. **Smart Chunking**: 토큰 기반 의미 단위 분할
4. **Local Embedding**: BGE-M3 모델로 로컬 임베딩 생성
5. **Vector Storage**: pgvector 최적화된 저장

## 기술 스택

### Core Framework
- **API Server**: FastAPI with async support
- **AI Orchestration**: LangGraph (workflow management)
- **Real-time**: Server-Sent Events (SSE) streaming
- **Configuration**: Pydantic Settings with .env support
- **Language**: Python 3.13+

### AI & ML
- **LLM**: OpenAI GPT-4o (답변 생성/회의록/Supervisor), GPT-4o-mini (분류/요약/인텐트 감지)
- **STT**: WhisperX (전사 + 화자 분리)
- **Embedding**: BGE-M3 (로컬 추론)
- **Document Parsing**: LlamaParser + custom parsers
- **Token Counting**: tiktoken (로컬, API 비용 없음)

### Tools & External Services
- **DuckDuckGo**: 웹 검색 (RAG 폴백)
- **Arxiv**: 논문 검색
- **Gmail**: 이메일 연동

### Database & Storage
- **Database**: PostgreSQL with async SQLAlchemy
- **Vector Store**: pgvector extension
- **Checkpointer**: PostgreSQL-based workflow state (thread_id 단위)
- **File Storage**: Local filesystem with structured organization

### Infrastructure
- **Container**: Docker Compose for services
- **Process Management**: asyncio + ThreadPoolExecutor
- **Error Handling**: Structured exception handling
- **Logging**: Structured logging with levels
- **Testing**: pytest with async support

## 프로젝트 구조

```
├── main.py                               # FastAPI 앱 진입점
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── chat.py                  # 채팅 API (SSE 스트리밍)
│   │       ├── documents.py             # 문서 업로드/관리 API
│   │       ├── search.py                # 검색 API
│   │       ├── meeting.py               # 회의록 API
│   │       └── users.py                 # 사용자 API
│   ├── agents/
│   │   ├── constants.py                 # WorkflowSteps, AgentTypes, StreamMessages
│   │   ├── state.py                     # RouterState, RAGState, MeetingState
│   │   ├── core/
│   │   │   ├── llm_provider.py          # gpt4o, gpt4o_mini 인스턴스
│   │   │   ├── agent_factory.py         # 범용 Agent 생성 팩토리
│   │   │   └── tool_node.py             # ToolNode 빌더
│   │   ├── edges/
│   │   │   ├── router/
│   │   │   │   ├── token_router.py      # 토큰 초과 여부 분기
│   │   │   │   └── agent_router.py      # agent_type 기반 라우팅
│   │   │   └── rag/
│   │   │       ├── internal_relevance.py # 내부 검색 관련성 평가
│   │   │       └── web_relevance.py      # 웹 검색 관련성 평가
│   │   ├── nodes/
│   │   │   ├── router/
│   │   │   │   ├── supervisor.py        # Supervisor 노드 (LLM 기반 라우팅)
│   │   │   │   ├── summarize.py         # 요약 노드 (messages 직접 교체)
│   │   │   │   ├── chat_agent.py        # Chat Sub Agent 진입점
│   │   │   │   ├── rag_agent.py         # RAG Sub Agent 진입점
│   │   │   │   ├── meeting_agent.py     # Meeting Sub Agent 진입점
│   │   │   │   └── final_response_agent.py # 최종 응답 정리
│   │   │   ├── chat/
│   │   │   │   ├── classifier.py        # 질문 분류 (gpt-4o-mini)
│   │   │   │   ├── generator.py         # 답변 생성 (gpt-4o · SSE)
│   │   │   │   └── router.py            # 질문 유형 라우터
│   │   │   ├── rag/
│   │   │   │   ├── rewrite.py           # 쿼리 재정의
│   │   │   │   ├── internal_search.py   # pgvector 내부 검색
│   │   │   │   ├── web_search.py        # DuckDuckGo 웹 검색
│   │   │   │   └── answer.py            # 최종 답변 생성
│   │   │   └── meeting/
│   │   │       ├── transcribe_audio.py  # WhisperX STT + 화자 분리
│   │   │       ├── merge_transcript.py  # 전사 결과 병합
│   │   │       └── generate_minutes.py  # 회의록 생성
│   │   ├── prompts/
│   │   │   ├── chat.py                  # 채팅 프롬프트
│   │   │   ├── router.py                # Supervisor · 요약 프롬프트
│   │   │   ├── rag.py                   # CRAG 프롬프트
│   │   │   └── meeting.py               # 회의록 프롬프트
│   │   ├── tools/
│   │   │   ├── internal_search.py       # pgvector 검색 Tool
│   │   │   ├── duckduckgo.py            # DuckDuckGo 검색 Tool
│   │   │   ├── arxiv.py                 # Arxiv 논문 검색 Tool
│   │   │   └── gmail.py                 # Gmail 연동 Tool
│   │   ├── workflows/
│   │   │   ├── router_workflow.py       # 최상위 Router Workflow (Supervisor)
│   │   │   ├── chat_workflow.py         # Chat Sub Agent 서브그래프
│   │   │   ├── rag_workflow.py          # CRAG Sub Agent 서브그래프
│   │   │   └── meeting_workflow.py      # Meeting Sub Agent 서브그래프
│   │   └── infra/
│   │       └── checkpointer.py          # PostgreSQL checkpointer
│   ├── infra/
│   │   ├── ai/
│   │   │   ├── embedding_service.py     # BGE-M3 임베딩
│   │   │   └── whisperx_manager.py      # WhisperX 모델 매니저 (싱글톤)
│   │   ├── parsers/                     # 문서 파서 시스템
│   │   │   ├── factory.py               # 파서 팩토리 (MIME 타입 매핑)
│   │   │   ├── pdf_parser.py            # PDF (PyMuPDF + PyPDF2)
│   │   │   ├── docx_parser.py           # DOCX (python-docx)
│   │   │   ├── xlsx_parser.py           # XLSX (openpyxl)
│   │   │   ├── csv_parser.py            # CSV (다중 인코딩)
│   │   │   └── doc_parser.py            # DOC (docx2txt/antiword)
│   │   └── storage/                     # 파일 저장소
│   ├── core/
│   │   ├── config.py                    # 환경 설정 (pydantic-settings)
│   │   ├── exceptions.py                # 커스텀 예외
│   │   ├── exception_handlers.py        # FastAPI 예외 핸들러
│   │   └── logging.py                   # 로깅 설정
│   ├── models/                          # SQLAlchemy ORM 모델
│   ├── schemas/                         # Pydantic API 스키마
│   ├── services/                        # 비즈니스 로직
│   └── db/                              # 데이터베이스 연결
├── notebook/
│   ├── workflow/
│   │   └── test_router_workflow.ipynb   # Router + Meeting 통합 테스트
│   ├── embedding/                       # 임베딩 관련 노트북
│   └── tools/                           # 툴 테스트 노트북
├── architecture/
│   └── route_architecture.html          # 아키텍처 시각화
├── data/
│   ├── documents/                       # 업로드된 문서
│   ├── models/                          # AI 모델 캐시
│   └── test/                            # 테스트용 파일
├── docker/
│   └── docker-compose.infra.yml         # PostgreSQL + pgvector
├── .env                                 # 환경 변수
└── pyproject.toml                       # 의존성 관리
```

## 설치 및 실행

### 1. 환경 설정

```bash
git clone <repository-url>
cd ai-agent

# 의존성 설치 (uv 사용)
uv sync
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

주요 설정 항목:

```env
# API Keys (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here
LLAMA_CLOUD_API_KEY=llx-your-llamacloud-api-key-here
HF_TOKEN=hf_your-huggingface-token-here  # 화자 분리용

# Server
PORT=8888
HOST=0.0.0.0

# Database
POSTGRES_EXTERNAL_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_agent

# Token Management
SUMMARIZE_MAX_TOKENS=89600        # 128K의 70% - 요약 트리거
SUMMARIZE_MAX_SUMMARY_TOKENS=512  # 요약 결과 최대 토큰

# WhisperX (회의록 기능)
WHISPERX_MODEL=large-v2
WHISPERX_DEVICE=cpu               # cpu 또는 cuda
WHISPERX_LANGUAGE=ko
WHISPERX_BATCH_SIZE=16
WHISPERX_MAX_DURATION_MINUTES=120
WHISPERX_LONG_AUDIO_THRESHOLD_MINUTES=30
WHISPERX_CHUNK_DURATION_MINUTES=10
```

### 3. 인프라 서비스 실행

```bash
docker compose --env-file .env -f docker/docker-compose.infra.yml up -d
```

### 4. 서버 실행

```bash
python main.py
```

- API 문서: http://localhost:8888/docs
- ReDoc: http://localhost:8888/redoc

## API 사용법

### Chat (문서 기반 질의응답)

```bash
curl -X POST "http://localhost:8888/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Python에 대해 자세히 설명해주세요",
    "user_id": "user123",
    "session_id": "session456"
  }' --no-buffer
```

### Meeting (회의록 자동 생성)

```bash
curl -X POST "http://localhost:8888/meeting/upload" \
  -F "audio_file=@meeting.mp3" \
  -F "title=팀 회의"
```

### Document Upload

```bash
curl -X POST "http://localhost:8888/documents/upload" \
  -F "file=@document.pdf" \
  -F "title=샘플 문서"
```

## 현재 구현 상태

### 완료된 기능

- **Core Infrastructure**: FastAPI, PostgreSQL + pgvector, Docker Compose, 비동기 ORM
- **Supervisor 패턴**: LLM 기반 동적 에이전트 라우팅, 토큰 초과 자동 요약
- **CRAG (Corrective RAG)**: 내부 검색 → 관련성 평가 → 웹 검색 폴백
- **Chat Sub Agent**: 질문 분류(FACT/SUMMARY/COMPARE/EVIDENCE) + RAG 답변 생성 + SSE 스트리밍
- **Meeting Sub Agent**: WhisperX STT + 화자 분리 + AI 회의록 생성 (최대 2시간)
- **External Tools**: Gmail, Arxiv, DuckDuckGo Tool 연동
- **Document Processing**: 멀티 포맷 파서 시스템 (PDF/DOC/DOCX/XLSX/CSV) + LlamaParser
- **Vector Search**: 의미적/하이브리드 검색, BGE-M3 로컬 임베딩
- **Exception Handling**: 구조화된 에러 응답 + 포괄적 예외 핸들러
- **Testing**: pytest 기반 테스트 + 노트북 통합 테스트

### 진행 중 / 예정

- 검색 결과 리랭킹
- 다국어 STT 지원 확장
- Redis 캐싱 레이어
- 사용자 인증 및 권한 관리

## 테스트

```bash
# 전체 테스트
python -m pytest

# 상세 출력
python -m pytest -v

# 커버리지 포함
python -m pytest --cov=app tests/
```

노트북 테스트: `notebook/workflow/test_router_workflow.ipynb`

## 라이센스

MIT License
