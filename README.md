# AI Agent System

다양한 AI 기술을 실험하고 학습하기 위한 포괄적인 AI 에이전트 시스템입니다.

## 프로젝트 개요

현업에서 활용되는 다양한 AI 기술들을 학습하고 실험하기 위한 플랫폼입니다. 현재는 RAG 시스템을 중심으로 구현되어 있지만, 향후 다양한 AI 에이전트 기능들을 확장해나갈 예정입니다.

이 프로젝트는 AI Agent 기반 기능들을 체계적으로 연구하고 개발하기 위한 목적으로 만들어졌습니다. RAG(Retrieval-Augmented Generation), MCP(Model Context Protocol), STT(Speech-to-Text), LangGraph 워크플로우 등 다양한 기술 스택을 단계적으로 구현하며 학습합니다.

## 아키텍처

```
[ Client ]
    |
[ FastAPI ]
    |
[ Services Layer ]
    ├─ Document Service (업로드, 처리)
    ├─ Embedding Service (BGE-M3)
    ├─ File Storage Service  
    ├─ Search Service (의미적/하이브리드 검색)
    └─ Chat Workflow (LangGraph)
    |
[ Database Layer ]
    ├─ PostgreSQL (문서 메타데이터)
    └─ pgvector (벡터 저장소)
```

### 현재 구현된 워크플로우
1. **Document Upload**: PDF, TXT, DOCX 파일 업로드 및 처리
2. **Text Processing**: LangChain을 사용한 문서 청킹
3. **Embedding Generation**: BGE-M3 모델 로컬 임베딩 생성
4. **Vector Storage**: pgvector 코사인 유사도 검색
5. **Semantic Search**: 의미적 검색 및 하이브리드 검색
6. **Chat Workflow**: LangGraph 기반 질문 분류 및 답변 생성

## 기술 스택

- **Framework**: FastAPI
- **AI Orchestration**: LangGraph
- **LLM**: OpenAI GPT-4o-mini
- **Embedding Model**: BGE-M3 (로컬 추론)
- **Vector Database**: PostgreSQL with pgvector
- **Text Processing**: LangChain
- **Configuration**: Pydantic Settings
- **Language**: Python 3.13+

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
- 문서 업로드 API (PDF, TXT, DOCX 지원)
- **LlamaParser 통합** - PDF/Excel/PowerPoint/Word 고품질 마크다운 변환 (새로 추가)
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

#### Testing & Quality Assurance
- **포괄적인 예외 핸들러 테스트 스위트** (새로 추가)
- **pytest 설정 및 테스트 환경 구성** (새로 추가)

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
│   │       ├── chat.py              # 채팅 API
│   │       ├── documents.py         # 문서 업로드/관리 API
│   │       ├── search.py            # 검색 API
│   │       └── users.py             # 사용자 API
│   ├── agents/
│   │   ├── nodes/                   # LangGraph 노드
│   │   ├── prompts/                 # 프롬프트 템플릿
│   │   ├── workflows/               # 워크플로우 정의
│   │   └── state.py                 # 상태 관리
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
│   │   ├── ai/                      # AI 관련 (임베딩)
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

`.env` 파일을 생성하고 다음 설정을 추가하세요:

```env
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Configuration
POSTGRES_EXTERNAL_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_agent
POSTGRES_HOST=localhost

# Embedding Configuration
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSIONS=1024
EMBEDDING_DEVICE=cpu
EMBEDDING_CACHE_DIR=./data/models

# Document Processing
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_FILE_SIZE_MB=50

# File Storage
FILE_STORAGE_PATH=./data/documents
ALLOWED_FILE_TYPES=pdf,txt,docx

# Agent Models
CLASSIFIER_MODEL=gpt-4o-mini
CLASSIFIER_TEMPERATURE=0.1
GENERATOR_MODEL=gpt-4o-mini
GENERATOR_TEMPERATURE=0.7
```

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
- API 문서: http://localhost:8000/docs
- ReDoc 문서: http://localhost:8000/redoc

## API 사용법

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

### 3. 채팅 에이전트

**POST /chat/**

사용자 메시지를 처리하고 AI 응답을 반환합니다.

```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Python이란 무엇인가요?",
    "user_id": "user123",
    "session_id": "session456"
  }'
```

**POST /chat/stream**

실시간 스트리밍 채팅 응답을 받습니다 (SSE).

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Python에 대해 자세히 설명해주세요"
  }' \
  --no-buffer
```

### 4. 시스템 상태 확인

**GET /search/stats**

검색 시스템 통계를 확인합니다.

```bash
curl http://localhost:8000/search/stats
```

## 설정

### 모델 설정
환경 변수를 통해 각 에이전트별 모델과 temperature를 설정할 수 있습니다:

- `CLASSIFIER_MODEL`: 질문 분류에 사용할 모델
- `CLASSIFIER_TEMPERATURE`: 분류 시 사용할 temperature (낮을수록 일관성↑)
- `GENERATOR_MODEL`: 답변 생성에 사용할 모델
- `GENERATOR_TEMPERATURE`: 답변 생성 시 사용할 temperature (높을수록 창의성↑)

### 프롬프트 커스터마이징
`app/agents/prompts/` 디렉토리의 템플릿 파일을 수정하여 프롬프트를 커스터마이징할 수 있습니다.

## 향후 계획

### Phase 1: RAG 시스템 구현 ✅
- [x] PostgreSQL + pgvector 데이터베이스 연동
- [x] BGE-M3 로컬 임베딩 모델 통합
- [x] 문서 업로드 및 처리 파이프라인
- [x] 의미적 검색 (Semantic Search) 구현
- [x] 하이브리드 검색 (키워드 + 의미적) 구현
- [x] 문서 청킹 및 메타데이터 관리
- [x] 검색 통계 및 모니터링
- [ ] 검색 결과 리랭킹 시스템

### Phase 2: MCP(Model Context Protocol) 활용
- [ ] MCP 서버 구현 및 연동
- [ ] 외부 도구 및 API 통합 (웹 검색, 계산기 등)
- [ ] 다중 컨텍스트 관리
- [ ] 도구 선택 및 실행 에이전트
- [ ] MCP 기반 워크플로우 확장

### Phase 3: STT 및 음성 처리 기능
- [ ] 음성 입력 처리 (Speech-to-Text)
- [ ] 실시간 음성 스트리밍 처리
- [ ] 다국어 음성 인식 지원
- [ ] 음성 감정 분석
- [ ] TTS(Text-to-Speech) 응답 생성

### Phase 4: 고급 에이전트 기능
- [ ] 검색 전략 선택 에이전트
- [ ] 증거 기반 답변 생성 및 출처 추적
- [ ] 멀티모달 입력 처리 (텍스트, 음성, 이미지)
- [ ] 대화 컨텍스트 관리 및 메모리
- [ ] 개인화 추천 시스템

### Phase 5: 인프라 및 운영
- [x] PostgreSQL 연동 및 데이터 관리
- [x] 구조화된 로깅 시스템
- [x] Docker Compose 인프라 구성
- [ ] Redis 캐싱 시스템
- [ ] 사용자 피드백 수집 및 분석
- [ ] 답변 품질 평가 메트릭
- [ ] Kubernetes 배포
- [ ] 모니터링 및 알림 시스템

## 기여

프로젝트에 기여하고 싶으시다면 Pull Request를 보내주세요.

## 라이센스

MIT License