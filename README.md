# AI Agent RAG System

LangGraph 기반의 에이전트 구동 질문 분류 및 답변 생성 시스템입니다.

## 프로젝트 개요

사용자 질문을 지능적으로 분류하고 적절한 답변을 생성하는 AI 에이전트 시스템입니다. LangGraph를 활용하여 질문 분류 → 답변 생성의 워크플로우를 구현했습니다.

이 프로젝트는 최근 기업들이 구현하고 있는 AI Agent 기반 기능들을 연습하고 학습하기 위한 목적으로 개발되었습니다. RAG(Retrieval-Augmented Generation), MCP(Model Context Protocol), STT(Speech-to-Text) 등 현업에서 활용되는 다양한 AI 기술들을 단계적으로 구현해볼 예정입니다.

## 아키텍처

```
[ Client ]
    |
[ FastAPI ]
    |
[ LangGraph Workflow ]
    ├─ Question Classifier Agent
    └─ Answer Generator Agent
```

### 워크플로우
1. **Question Classifier**: 사용자 질문을 4개 카테고리로 분류
2. **Answer Generator**: 질문 유형에 따라 맞춤형 답변 생성

## 기술 스택

- **Framework**: FastAPI
- **AI Orchestration**: LangGraph
- **LLM**: OpenAI GPT-4o-mini
- **Vector Database**: PostgreSQL with pgvector
- **Configuration**: Pydantic Settings
- **Language**: Python 3.13+

## 현재 구현 상태

### ✅ 완료된 기능
- FastAPI 웹 서버 설정
- LangGraph 워크플로우 구현
- 질문 분류 에이전트 (4개 카테고리: FACT, SUMMARY, COMPARE, EVIDENCE)
- 답변 생성 에이전트 (카테고리별 맞춤 프롬프트)
- 환경 변수 기반 모델 설정
- 프롬프트 템플릿 분리
- RESTful API 엔드포인트

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
│   │       ├── chat.py              # 채팅 API 엔드포인트
│   │       └── users.py             # 사용자 API 엔드포인트
│   ├── agents/
│   │   ├── nodes/
│   │   │   ├── classifier.py        # 질문 분류 에이전트
│   │   │   └── generator.py         # 답변 생성 에이전트
│   │   ├── prompts/
│   │   │   ├── classification.py    # 분류 프롬프트 템플릿
│   │   │   └── generation.py        # 생성 프롬프트 템플릿
│   │   ├── workflows/
│   │   │   └── chat_workflow.py     # LangGraph 워크플로우
│   │   └── state.py                 # 상태 정의
│   ├── schemas/
│   │   └── chat.py                  # Pydantic 모델
│   ├── core/
│   │   └── config.py                # 설정 관리
│   ├── db/                          # 데이터베이스 (미구현)
│   └── services/                    # 비즈니스 로직 (미구현)
├── .env                             # 환경 변수
├── pyproject.toml                   # 프로젝트 설정
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
OPENAI_API_KEY=your_openai_api_key_here
PORT=8888

# Database Configuration
POSTGRES_EXTERNAL_PORT=5433
POSTGRES_INTERNAL_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_agent

# Agent Node Models
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
- API 문서: http://localhost:8888/docs
- ReDoc 문서: http://localhost:8888/redoc

## API 사용법

### 채팅 엔드포인트

**POST /chat/**

사용자 메시지를 처리하고 AI 응답을 반환합니다.

```bash
curl -X POST "http://localhost:8888/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Python이란 무엇인가요?",
    "user_id": "user123",
    "session_id": "session456"
  }'
```

**Response:**
```json
{
  "answer": "Python은 고급 프로그래밍 언어입니다...",
  "session_id": "session456",
  "question_type": "FACT",
  "model_used": "gpt-4o-mini"
}
```

### 상태 확인 엔드포인트

**GET /chat/health**

채팅 서비스 상태를 확인합니다.

```bash
curl http://localhost:8888/chat/health
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

### Phase 1: RAG 검색 기능 구현
- [x] Vector Database (PostgreSQL with pgvector) 연동
- [ ] 문서 임베딩 및 벡터 저장
- [ ] 의미적 검색 (Semantic Search) 구현
- [ ] 하이브리드 검색 (키워드 + 벡터) 구현
- [ ] 문서 청킹 및 메타데이터 관리
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
- [ ] PostgreSQL 연동 및 데이터 관리
- [ ] Redis 캐싱 시스템
- [ ] 사용자 피드백 수집 및 분석
- [ ] 답변 품질 평가 메트릭
- [ ] Docker 컨테이너화
- [ ] Kubernetes 배포
- [ ] 모니터링 및 로깅 시스템

## 기여

프로젝트에 기여하고 싶으시다면 Pull Request를 보내주세요.

## 라이센스

MIT License