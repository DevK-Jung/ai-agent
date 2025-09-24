# AI Interface API

FastAPI 기반 AI 인터페이스 애플리케이션입니다. 문서 처리, 벡터 검색, LLM 통합 기능을 제공합니다.

## 📋 주요 기능

- **문서 처리**: PDF, DOCX, XLSX 등 다양한 포맷 지원
- **벡터 검색**: PostgreSQL + pgvector 기반 시맨틱 검색
- **LLM 통합**: Ollama를 통한 AI 모델 연동
- **코드 분석**: 코드베이스 인덱싱 및 검색
- **컬렉션 관리**: 문서 그룹화 및 관리
- **웹 인터페이스**: HTML 템플릿 기반 사용자 인터페이스

## 🛠 기술 스택

- **Backend**: FastAPI, Python 3.13+
- **Database**: PostgreSQL, pgvector
- **AI/ML**: Ollama, LangChain
- **문서 처리**: PyPDF, python-docx, pandas
- **기타**: SQLAlchemy, Pydantic, Uvicorn

## 📁 프로젝트 구조

```
ai-interface/
├── app/
│   ├── api/v1/                 # API v1 엔드포인트
│   │   └── endpoints/          # 각 도메인별 API 엔드포인트
│   ├── core/                   # 핵심 설정 및 유틸리티
│   │   ├── config/            # 애플리케이션 설정
│   │   ├── database/          # 데이터베이스 연결
│   │   ├── exception/         # 예외 처리
│   │   └── utils/             # 공통 유틸리티
│   ├── domains/               # 비즈니스 도메인
│   │   ├── code/              # 코드 분석 도메인
│   │   ├── collection/        # 컬렉션 관리
│   │   ├── document/          # 문서 처리
│   │   ├── file/              # 파일 관리
│   │   ├── llm/               # LLM 통합
│   │   ├── search/            # 검색 기능
│   │   └── vector_backup/     # 벡터 백업
│   ├── infra/                 # 인프라 레이어
│   │   ├── ai/                # AI 모델 연동
│   │   ├── code/              # 코드 처리
│   │   ├── docker/            # Docker 관련
│   │   └── vector_db/         # 벡터 데이터베이스
│   ├── view/                  # 웹 인터페이스
│   └── main.py                # 메인 애플리케이션
├── templates/                 # HTML 템플릿
├── tests/                     # 테스트 코드
├── scripts/                   # 유틸리티 스크립트
├── data/                      # 데이터 디렉토리
├── prompts/                   # AI 프롬프트
└── pyproject.toml            # 프로젝트 설정
```

## 🚀 설치 및 실행

### 1. 요구사항

- Python 3.13+
- PostgreSQL (pgvector 확장)
- Ollama

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd ai-interface

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -e .
```

### 3. 환경 설정

```bash
# 환경변수 파일 복사 및 수정
cp .env.example .env
```

주요 환경변수 설정:

```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/maindb
VECTOR_POSTGRES_HOST=localhost
VECTOR_POSTGRES_PORT=5433
VECTOR_POSTGRES_DB=vector

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3:567m-fp16

# 서버
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 4. 데이터베이스 설정

```bash
# PostgreSQL에서 pgvector 확장 활성화
# psql에서 실행:
CREATE EXTENSION vector;
```

### 5. 실행

```bash
# 개발 서버 실행
python app/main.py

# 또는 uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서 확인 가능:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Info**: http://localhost:8000/api

### 주요 엔드포인트

- `GET /api/v1/health` - 헬스체크
- `POST /api/v1/documents/upload` - 문서 업로드
- `POST /api/v1/search/similarity` - 벡터 유사도 검색
- `POST /api/v1/llm/chat` - LLM 채팅
- `GET /api/v1/collections` - 컬렉션 목록
- `POST /api/v1/code/analyze` - 코드 분석

## 🔧 개발

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_specific.py

# 커버리지와 함께 실행
pytest --cov=app
```

### 코드 품질

```bash
# 린트 체크 (설정된 경우)
ruff check app/

# 포맷팅 (설정된 경우)
ruff format app/
```

## 🌐 웹 인터페이스

웹 브라우저에서 `http://localhost:8000`에 접속하여 사용자 인터페이스 이용 가능

주요 화면:
- 문서 업로드 및 관리
- 벡터 검색
- LLM 채팅 인터페이스
- 컬렉션 관리

## 📖 사용 예제

### 문서 업로드

```python
import requests

files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/v1/documents/upload', files=files)
print(response.json())
```

### 벡터 검색

```python
import requests

data = {
    "query": "검색할 내용",
    "collection_name": "documents",
    "k": 5
}
response = requests.post('http://localhost:8000/api/v1/search/similarity', json=data)
print(response.json())
```

## 🐳 Docker

Docker를 사용한 실행도 지원됩니다:

```bash
# Docker Compose 실행 (설정된 경우)
docker-compose up -d
```

## 🤝 기여

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 🆘 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

**최신 업데이트**: 2024년 9월
**버전**: 1.0.0