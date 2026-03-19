# Plan: document_processor에서 LlamaParser 직접 사용

## 방향

`extract_text_from_file()`에서 `ParserFactory` 대신 `LlamaParserService`를 우선 사용한다.
LlamaParser가 지원하는 형식(PDF, DOCX, XLSX, PPTX)은 LlamaParser로,
지원하지 않는 형식(CSV, TXT)은 기존 `ParserFactory`로 처리한다.

```
extract_text_from_file(file_type)
  ├─ TXT          → 기존 _extract_from_txt() (변화 없음)
  ├─ LlamaParser 지원 (PDF, DOCX, XLSX, PPTX 등)
  │    └─ LlamaParserService.parse_to_markdown()
  └─ 나머지       → 기존 ParserFactory (CSV 등)
```

---

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `app/services/document_processor.py` | `extract_text_from_file()`에 LlamaParser 분기 추가 |

`pdf_parser.py`, `factory.py` 등 **다른 파일 변경 없음**.

---

## 세부 구현

### document_processor.py

```python
from app.infra.parsers.llama_parser import LlamaParserService, ProcessingTier

_llama_service = LlamaParserService()


async def extract_text_from_file(self, file_path: str, file_type: str) -> str:
    try:
        # TXT는 기존 방식 유지
        if file_type == "text/plain":
            return self._extract_from_txt(file_path)

        # LlamaParser 지원 형식이면 우선 사용
        if _llama_service.is_available() and _llama_service.is_supported_file_type(file_type):
            result = await _llama_service.parse_to_markdown(
                file_path=file_path,
                file_type=file_type,
                tier=ProcessingTier.COST_EFFECTIVE,
            )
            if result.get("success"):
                self.logger.info(f"LlamaParser 파싱 완료: {file_path}")
                return result["markdown"]
            raise RuntimeError(f"LlamaParser 파싱 실패: {result.get('error')}")

        # 나머지 형식은 기존 ParserFactory 사용
        if not ParserFactory.is_supported_mime_type(file_type):
            raise ValueError(f"지원하지 않는 파일 형식: {file_type}")

        parser = ParserFactory.get_parser(file_type)
        parsed_content = await parser.parse(file_path)
        return parsed_content.raw_text

    except Exception as e:
        self.logger.error(f"텍스트 추출 실패 ({file_path}): {e}")
        raise
```

---

## 설계 결정

| 결정 | 이유 |
|------|------|
| `document_processor`에서 분기 | 파서 내부가 아닌 orchestration 레이어에서 결정 — 역할 명확 |
| `_llama_service`를 모듈 레벨 싱글톤 | 매 요청마다 클라이언트 재초기화 방지 |
| `is_available()` 체크 | API 키 미설정 시 기존 ParserFactory로 자연스럽게 진행 |
| LlamaParser 실패 시 예외 raise | fallback 없음. 실패는 실패 |
