# AI Agent RAG System

Agent-based Explainable RAG (Retrieval-Augmented Generation) System - 엔터프라이즈급 다중 에이전트 AI 시스템입니다.

## 프로젝트 개요

단순한 RAG 데모를 넘어선 엔터프라이즈 수준의 아키텍처를 구현하는 프로젝트입니다. 질문 의도 이해, 검색 전략 선택, 증거 기반 답변 생성을 통한 설명 가능한 AI 시스템을 제공합니다.

**핵심 특징:**
- 🤖 **다중 에이전트 아키텍처**: Chat Agent + Meeting Agent로 구성된 라우팅 시스템
- 📄 **고급 문서 처리**: LlamaParser + 분리된 파서 시스템으로 고품질 텍스트 추출
- 🎙️ **회의록 자동 생성**: WhisperX STT + 화자 분리 + AI 회의록 작성
- ⚡ **실시간 스트리밍**: SSE 기반 실시간 응답 및 진행 상황 추적
- 🔍 **지능형 검색**: 질문 분류에 따른 맞춤형 검색 전략
- 📊 **확장 가능한 구조**: LangGraph 워크플로우 + PostgreSQL 체크포인터

## 아키텍처

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
    ├─ Meeting Sub Agent (STT + 화자 분리 + 회의록 생성)
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
    ├─ WhisperX Manager (스레드 안전 모델 캐싱)
    ├─ BGE-M3 Embedding Service
    └─ OpenAI LLM Services
    |
[ Database Layer ]
    ├─ PostgreSQL (문서, 대화 이력, 체크포인터)
    └─ pgvector (벡터 저장소)
```

### 구현된 워크플로우

#### 📄 Chat Workflow (문서 기반 질의응답)
```
need_prev_conversation (is_new_session 기반)
    → load_history_from_db 또는 check_token
    → summarize_conversation (8000토큰 초과시)
    → classify_question (FACT, SUMMARY, COMPARE, EVIDENCE)
    → generate_answer (카테고리별 맞춤 프롬프트)
    → save_message_to_db
```

#### 🎙️ Meeting Workflow (회의록 자동 생성)
```
audio_upload
    → transcribe_audio (WhisperX STT + 화자 분리)
        ├─ 긴 오디오 감지 (30분+ → 10분 청킹)
        ├─ 동적 배치 크기 조정
        └─ 스레드 안전 모델 캐싱
    → merge_transcript (화자별 발언 그룹화)
    → generate_minutes (구조화된 회의록 생성)
```

#### 📊 Document Processing
1. **Multi-format Upload**: PDF, DOC, DOCX, XLSX, CSV 지원
2. **High-quality Parsing**: LlamaParser + 분리된 파서 시스템
3. **Smart Chunking**: LangChain 기반 의미 단위 분할
4. **Local Embedding**: BGE-M3 모델로 로컬 임베딩 생성
5. **Vector Storage**: pgvector 최적화된 저장
6. **Intelligent Search**: 질문 유형별 맞춤 검색 전략

## 기술 스택

### 🔧 Core Framework
- **API Server**: FastAPI with async support
- **AI Orchestration**: LangGraph (workflow management)
- **Real-time**: Server-Sent Events (SSE) streaming
- **Configuration**: Pydantic Settings with .env support
- **Language**: Python 3.13+

### 🤖 AI & ML
- **LLM**: OpenAI GPT-4o (답변 생성), GPT-4o-mini (분류)
- **STT**: WhisperX (전사 + 화자 분리)
- **Embedding**: BGE-M3 (로컬 추론)
- **Document Parsing**: LlamaParser + custom parsers

### 💾 Database & Storage
- **Database**: PostgreSQL with async SQLAlchemy
- **Vector Store**: pgvector extension
- **Checkpointer**: PostgreSQL-based workflow state
- **File Storage**: Local filesystem with structured organization

### 🚀 Infrastructure
- **Container**: Docker Compose for services
- **Process Management**: asyncio + ThreadPoolExecutor
- **Error Handling**: Structured exception handling
- **Logging**: Structured logging with levels
- **Testing**: pytest with async support

## 현재 구현 상태

### ✅ 완료된 기능

#### Core Infrastructure
- FastAPI 웹 서버 설정
- PostgreSQL + pgvector 데이터베이스 설정
- SQLAlchemy 비동기 ORM 모델
- Docker Compose 인프라 구성
- 환경 변수 기반 설정 관리
- 구조화된 로깅 시스템
- **FastAPI 예외 핸들러 시스템** (새로 추가)
- **구조화된 에러 응답 스키마** (새로 추가)

#### Document Processing
- **다중 파일 형식 지원**: PDF, DOC, DOCX, XLSX, CSV 파일 업로드 및 처리
- **분리된 파서 시스템**: Factory 패턴 기반 파일별 최적화된 텍스트 추출
  - PDF 파서: PyMuPDF + PyPDF2 fallback
  - DOCX 파서: python-docx 기반 구조화된 텍스트 추출
  - XLSX 파서: openpyxl 기반 시트별 테이블 데이터 처리
  - CSV 파서: 다중 인코딩 지원 (CP949, EUC-KR, UTF-8)
  - DOC 파서: docx2txt/antiword/olefile 지원 (레거시 Word 문서)
- **LlamaParser 통합** - PDF/Excel/PowerPoint/Word 고품질 마크다운 변환
- BGE-M3 모델 로컬 임베딩 생성
- LangChain 기반 문서 청킹
- 문서 메타데이터 관리
- 백그라운드 문서 처리 태스크

#### Search & Retrieval
- pgvector 코사인 유사도 검색
- 의미적 검색 (Semantic Search)
- 하이브리드 검색 (키워드 + 의미적)
- 검색 통계 및 모니터링

#### Chat & Agent
- LangGraph 워크플로우 구현
- 질문 분류 에이전트 (FACT, SUMMARY, COMPARE, EVIDENCE)
- 답변 생성 에이전트 (카테고리별 맞춤 프롬프트)
- 프롬프트 템플릿 분리
- **SSE(Server-Sent Events) 스트리밍 응답** (새로 추가)
- **실시간 워크플로우 진행 상태 추적** (새로 추가)
- **워크플로우 상수 및 메시지 분리** (새로 추가)

#### 🎙️ Meeting Agent (NEW)
- **WhisperX Integration**: STT + 화자 분리 통합
- **Long Audio Processing**: 긴 오디오 파일 청킹 처리 (최대 2시간)
- **Thread-safe Model Caching**: FastAPI lifespan 기반 모델 관리
- **Dynamic Batch Sizing**: 오디오 길이에 따른 배치 크기 자동 조정
- **Speaker Diarization**: pyannote 기반 화자 식별
- **Intelligent Transcript Merging**: 화자별 발언 그룹화
- **AI Meeting Minutes**: LLM 기반 구조화된 회의록 자동 생성

#### 🏗️ Infrastructure Improvements
- **Enhanced Error Handling**: 구조화된 예외 핸들러 + 테스트 스위트
- **Configuration Management**: 완전한 .env 기반 설정 관리
- **Thread Safety**: 모델 캐싱 및 동시성 처리 개선
- **Real-time Monitoring**: SSE를 통한 워크플로우 진행 상황 추적

### 질문 분류 카테고리
- **FACT**: 구체적인 사실이나 정보를 묻는 질문
- **SUMMARY**: 요약을 요청하는 질문
- **COMPARE**: 비교를 요청하는 질문
- **EVIDENCE**: 근거나 증거를 요구하는 질문

## 프로젝트 구조

```
├── main.py                           # FastAPI 앱 진입점
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── chat.py              # 채팅 API (SSE 스트리밍)
│   │       ├── documents.py         # 문서 업로드/관리 API
│   │       ├── search.py            # 검색 API
│   │       ├── meeting.py           # 회의록 API ⭐ NEW
│   │       └── users.py             # 사용자 API
│   ├── agents/
│   │   ├── constants.py             # 워크플로우 상수 및 메시지
│   │   ├── nodes/                   # LangGraph 노드
│   │   │   ├── chat/                # 채팅 에이전트 노드
│   │   │   └── meeting/             # 회의록 에이전트 노드 ⭐ NEW
│   │   │       ├── transcribe_audio.py    # WhisperX STT + 화자 분리
│   │   │       ├── merge_transcript.py     # 전사 결과 병합
│   │   │       └── generate_minutes.py    # 회의록 생성
│   │   ├── prompts/                 # 프롬프트 템플릿
│   │   │   ├── chat.py              # 채팅 프롬프트
│   │   │   └── meeting.py           # 회의록 프롬프트 ⭐ NEW
│   │   ├── workflows/               # 워크플로우 정의
│   │   │   ├── chat_workflow.py     # 채팅 워크플로우
│   │   │   └── meeting_workflow.py  # 회의록 워크플로우 ⭐ NEW
│   │   ├── infra/                   # 에이전트 인프라
│   │   └── state.py                 # 상태 관리 (ChatState, MeetingState)
│   ├── models/                      # SQLAlchemy ORM 모델
│   │   └── document.py              # Document, DocumentChunk
│   ├── schemas/                     # Pydantic 스키마
│   │   ├── chat.py                  # 채팅 관련
│   │   ├── document.py              # 문서 관련
│   │   └── search.py                # 검색 관련
│   ├── services/                    # 비즈니스 로직
│   │   ├── document_service.py      # 문서 처리
│   │   └── search_service.py        # 검색 서비스
│   ├── infra/                       # 인프라 서비스
│   │   ├── ai/                      # AI 관련 서비스
│   │   │   ├── embedding_service.py # BGE-M3 임베딩
│   │   │   └── whisperx_manager.py  # WhisperX 모델 매니저 ⭐ NEW
│   │   ├── parsers/                 # 문서 파서 시스템
│   │   │   ├── __init__.py          # ParserFactory export
│   │   │   ├── factory.py           # 파서 팩토리
│   │   │   ├── base.py              # BaseParser 추상 클래스
│   │   │   ├── models.py            # ParsedContent 모델
│   │   │   ├── pdf_parser.py        # PDF 파서
│   │   │   ├── docx_parser.py       # DOCX 파서
│   │   │   ├── xlsx_parser.py       # XLSX 파서
│   │   │   ├── csv_parser.py        # CSV 파서
│   │   │   └── doc_parser.py        # DOC 파서
│   │   └── storage/                 # 파일 저장소
│   ├── dependencies/                # 의존성 주입
│   ├── core/                        # 핵심 설정
│   │   ├── config.py                # 환경 설정
│   │   └── logging.py               # 로깅 설정
│   ├── db/                          # 데이터베이스
│   └── utils/                       # 유틸리티
├── data/                            # 데이터 저장소
│   ├── documents/                   # 업로드된 문서
│   └── models/                      # AI 모델 캐시
├── docker/
│   └── docker-compose.infra.yml     # 인프라 서비스
├── .env                             # 환경 변수
├── pyproject.toml                   # 의존성 관리
└── README.md
```

## 설치 및 실행

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd ai-agent

# 의존성 설치 (uv 사용)
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 `.env`로 복사하고 실제 값을 입력하세요:

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

# WhisperX (회의록 기능)
WHISPERX_MODEL=large-v2              # 모델 크기
WHISPERX_DEVICE=cpu                  # cpu 또는 cuda
WHISPERX_LANGUAGE=ko                 # 기본 언어
WHISPERX_BATCH_SIZE=16               # 배치 크기
WHISPERX_MAX_DURATION_MINUTES=120    # 최대 2시간
WHISPERX_LONG_AUDIO_THRESHOLD_MINUTES=30  # 긴 오디오 기준
WHISPERX_CHUNK_DURATION_MINUTES=10   # 청킹 단위

# AI Models
CLASSIFIER_MODEL=gpt-4o-mini
GENERATOR_MODEL=gpt-4o
MINUTES_MODEL=gpt-4o
```

> 📋 전체 설정 항목은 `.env.example` 파일을 참고하세요.

### 3. 인프라 서비스 실행 (PostgreSQL with pgvector)

```bash
# PostgreSQL with pgvector 실행
docker compose --env-file .env -f docker/docker-compose.infra.yml up -d

# 서비스 상태 확인
docker compose -f docker/docker-compose.infra.yml ps
```

### 4. 서버 실행

```bash
python main.py
```

서버가 실행되면 다음 URL에서 접근할 수 있습니다:
- API 문서: http://localhost:8888/docs
- ReDoc 문서: http://localhost:8888/redoc

## 🎯 주요 기능

### 📄 문서 기반 질의응답
- **지능형 질문 분류**: FACT, SUMMARY, COMPARE, EVIDENCE
- **맞춤형 검색 전략**: 질문 유형별 최적화된 검색
- **실시간 스트리밍**: SSE 기반 점진적 응답
- **대화 컨텍스트**: 이전 대화 기반 연속성 유지

### 🎙️ 회의록 자동 생성
- **고품질 STT**: WhisperX 기반 정확한 음성 인식
- **화자 분리**: 발언자별 구분된 전사
- **긴 오디오 처리**: 최대 2시간, 10분 단위 청킹
- **AI 회의록**: 구조화된 회의록 자동 생성
- **진행 상황 추적**: 실시간 처리 상태 확인

### 🔧 시스템 특징
- **확장 가능한 아키텍처**: 에이전트 기반 모듈식 설계
- **엔터프라이즈 품질**: 구조화된 에러 처리, 로깅, 모니터링
- **설정 관리**: 완전한 환경 변수 기반 설정
- **성능 최적화**: 모델 캐싱, 비동기 처리, 스레드 안전성

## API 사용법

### 🎯 Chat Agent (문서 기반 질의응답)

### 1. 문서 업로드

**POST /documents/upload**

문서를 업로드하고 임베딩 처리를 수행합니다.

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf" \
  -F "title=샘플 문서"
```

### 2. 문서 검색

**POST /search/semantic**

의미적 검색을 수행합니다.

```bash
curl -X POST "http://localhost:8000/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python 프로그래밍에 대해 알려주세요",
    "limit": 5,
    "threshold": 0.7
  }'
```

**POST /search/hybrid**

하이브리드 검색(의미적 + 키워드)을 수행합니다.

```bash
curl -X POST "http://localhost:8000/search/hybrid?semantic_weight=0.7&keyword_weight=0.3" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python",
    "limit": 10
  }'
```

### 🎙️ Meeting Agent (회의록 자동 생성)

**POST /meeting/upload**

오디오 파일을 업로드하고 회의록을 자동 생성합니다.

```bash
curl -X POST "http://localhost:8888/meeting/upload" \
  -F "audio_file=@meeting.wav" \
  -F "title=팀 회의 2024-02-23"
```

**GET /meeting/stream/{workflow_id}**

회의록 생성 진행 상황을 실시간으로 확인합니다 (SSE).

```bash
curl "http://localhost:8888/meeting/stream/{workflow_id}" \
  --no-buffer
```

**Response Example:**
```json
{
  "workflow_id": "meeting_20240223_143052",
  "status": "completed",
  "transcript": "Speaker 1: 안녕하세요...",
  "minutes": "# 회의록\n\n## 참석자\n- Speaker 1\n- Speaker 2\n\n## 주요 논의사항\n..."
}
```

### 💬 Chat Agent (문서 기반 질의응답)

**POST /chat/stream**

실시간 스트리밍 채팅 응답을 받습니다.

```bash
curl -X POST "http://localhost:8888/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Python에 대해 자세히 설명해주세요",
    "user_id": "user123",
    "session_id": "session456"
  }' \
  --no-buffer
```

### 4. 시스템 상태 확인

**GET /search/stats**

검색 시스템 통계를 확인합니다.

```bash
curl http://localhost:8000/search/stats
```

## ⚙️ 고급 설정

### AI 모델 설정
환경 변수로 각 에이전트별 모델과 파라미터를 세밀하게 조정할 수 있습니다:

```env
# Chat Agent Models
CLASSIFIER_MODEL=gpt-4o-mini          # 질문 분류 (빠른 처리)
CLASSIFIER_TEMPERATURE=0.1            # 낮을수록 일관성↑
GENERATOR_MODEL=gpt-4o               # 답변 생성 (고품질)
GENERATOR_TEMPERATURE=0.7            # 높을수록 창의성↑

# Meeting Agent Models  
MINUTES_MODEL=gpt-4o                 # 회의록 생성
MINUTES_TEMPERATURE=0.3              # 구조화된 출력
```

### WhisperX 최적화
오디오 처리 성능을 환경에 맞게 튜닝:

```env
# 모델 크기 (정확도 vs 속도)
WHISPERX_MODEL=large-v2              # tiny, base, small, medium, large-v2

# 하드웨어 설정
WHISPERX_DEVICE=cuda                 # GPU 사용 시 cuda
WHISPERX_BATCH_SIZE=32               # GPU 메모리에 따라 조정

# 긴 오디오 처리
WHISPERX_MAX_DURATION_MINUTES=120    # 최대 길이 제한
WHISPERX_LONG_AUDIO_THRESHOLD_MINUTES=30  # 청킹 시작 기준
WHISPERX_CHUNK_DURATION_MINUTES=10   # 청크 크기
```

### 프롬프트 커스터마이징
- **Chat Prompts**: `app/agents/prompts/chat.py`
- **Meeting Prompts**: `app/agents/prompts/meeting.py`

각 에이전트별 프롬프트를 수정하여 도메인 특화 응답을 구현할 수 있습니다.

### 데이터베이스 최적화
```env
# 연결 풀 설정 (동시 사용자 수에 따라 조정)
DB_POOL_SIZE=10
DB_POOL_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## 구현 현황 및 로드맵

### ✅ Phase 1: Core RAG System (완료)
- [x] PostgreSQL + pgvector 벡터 데이터베이스
- [x] BGE-M3 로컬 임베딩 모델
- [x] LlamaParser + 멀티 파서 시스템
- [x] 의미적/하이브리드 검색
- [x] LangGraph 기반 질문 분류 및 답변 생성
- [x] SSE 실시간 스트리밍
- [x] 구조화된 예외 처리

### ✅ Phase 2: Meeting Agent (완료)
- [x] WhisperX STT + 화자 분리 통합
- [x] 긴 오디오 파일 청킹 처리 (최대 2시간)
- [x] 스레드 안전 모델 캐싱
- [x] 동적 배치 크기 조정
- [x] AI 기반 회의록 자동 생성
- [x] 실시간 진행 상황 모니터링

### 🔄 Phase 3: Advanced Features (진행 중)
- [ ] 검색 결과 리랭킹 시스템
- [ ] 다국어 STT 지원 확장
- [ ] 회의록 템플릿 커스터마이징
- [ ] 사용자 피드백 수집
- [ ] 답변 품질 평가 메트릭

### 📋 Phase 4: Enterprise Features (계획)
- [ ] Redis 캐싱 레이어
- [ ] 사용자 인증 및 권한 관리
- [ ] 멀티테넌트 지원
- [ ] API 사용량 모니터링
- [ ] Kubernetes 배포 설정

### 🚀 Phase 5: Advanced AI (미래)
- [ ] MCP(Model Context Protocol) 통합
- [ ] 멀티모달 입력 처리 (텍스트, 음성, 이미지)
- [ ] 개인화 추천 시스템
- [ ] 실시간 음성 대화
- [ ] 감정 분석 및 컨텍스트 이해

## 🤝 기여하기

이 프로젝트는 AI Agent 기술의 실무 적용을 목표로 하며, 다음과 같은 기여를 환영합니다:

- 🐛 **버그 리포트**: Issues를 통한 버그 신고
- 💡 **기능 제안**: 새로운 에이전트나 기능 아이디어
- 🔧 **코드 개선**: 성능 최적화, 코드 품질 향상
- 📚 **문서화**: 사용법, 설정 가이드 개선
- 🧪 **테스트**: 테스트 케이스 추가 및 개선

### 개발 환경 설정
```bash
# 개발 의존성 설치
uv sync --dev

# 테스트 실행
python -m pytest

# 코드 품질 검사
ruff check .
ruff format .
```

## 📄 라이센스

MIT License - 자유롭게 사용, 수정, 배포할 수 있습니다.

## 🆘 지원

- 📖 **Documentation**: [API 문서](http://localhost:8888/docs)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: 기술적 질문이나 아이디어 공유

---

> 🚀 **Enterprise-grade AI Agent System** - 실무에서 바로 사용할 수 있는 수준의 AI 시스템을 구현하고 있습니다.