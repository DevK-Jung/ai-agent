import hashlib
import logging
from typing import List, Dict, Any

from langchain_core.documents import Document as LangChainDocument
# LangChain text splitters
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.token_utils import count_tokens

from app.core.config import settings
from app.infra.parsers import ParserFactory


class DocumentProcessor:
    """문서 처리 및 청킹 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 토큰 기반 텍스트 분할기 설정
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=count_tokens,  # 토큰 기반 청킹
            separators=settings.CHUNK_SEPARATORS_LIST
        )

    async def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        파일에서 텍스트를 추출합니다.
        
        Args:
            file_path: 파일 경로
            file_type: 파일 MIME 타입
            
        Returns:
            str: 추출된 텍스트
        """
        try:
            # 텍스트 파일은 간단하게 직접 처리
            if file_type == "text/plain":
                return self._extract_from_txt(file_path)
            
            # 지원 여부 확인
            if not ParserFactory.is_supported_mime_type(file_type):
                raise ValueError(f"지원하지 않는 파일 형식: {file_type}")
            
            # 적절한 파서를 사용하여 파싱
            parser = ParserFactory.get_parser(file_type)
            parsed_content = await parser.parse(file_path)
            
            self.logger.info(f"파일 파싱 완료: {file_path} (테이블: {len(parsed_content.tables)}개, 이미지: {len(parsed_content.images)}개)")
            
            return parsed_content.raw_text

        except Exception as e:
            self.logger.error(f"텍스트 추출 실패 ({file_path}): {e}")
            raise

    def _extract_from_txt(self, file_path: str) -> str:
        """TXT 파일에서 텍스트 추출"""
        encodings = ['utf-8', 'cp949', 'latin-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise ValueError(f"텍스트 파일 인코딩을 식별할 수 없습니다: {file_path}")


    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        텍스트를 청크로 분할합니다.
        
        Args:
            text: 분할할 텍스트
            metadata: 추가 메타데이터
            
        Returns:
            List[Dict]: 청크 정보 리스트
        """
        if not text.strip():
            return []

        try:
            # LangChain Document 생성
            doc = LangChainDocument(
                page_content=text,
                metadata=metadata or {}
            )

            # 텍스트 분할
            chunks = self.text_splitter.split_documents([doc])

            # 청크 정보 생성
            chunk_data = []
            for i, chunk in enumerate(chunks):
                content = chunk.page_content.strip()
                if not content:
                    continue

                chunk_info = {
                    "chunk_index": i,
                    "content": content,
                    "content_hash": self._generate_content_hash(content),
                    "char_count": len(content),
                    "token_count": self._estimate_token_count(content),
                    "chunk_type": "text",
                    "start_position": text.find(content) if content in text else 0,
                    "end_position": text.find(content) + len(content) if content in text else len(content),
                    "extra_metadata": chunk.metadata
                }

                chunk_data.append(chunk_info)

            self.logger.info(f"텍스트를 {len(chunk_data)}개 청크로 분할 완료")
            return chunk_data

        except Exception as e:
            self.logger.error(f"텍스트 청킹 실패: {e}")
            raise

    def _generate_content_hash(self, content: str) -> str:
        """콘텐츠 해시 생성"""
        return hashlib.sha256(content.encode()).hexdigest()

    def _estimate_token_count(self, text: str) -> int:
        """정확한 토큰 수 계산"""
        return count_tokens(text)

    def validate_file_content(self, text: str) -> bool:
        """
        추출된 텍스트의 유효성을 검증합니다.
        
        Args:
            text: 검증할 텍스트
            
        Returns:
            bool: 유효성 여부
        """
        if not text or not text.strip():
            return False

        # 최소 길이 체크
        if len(text.strip()) < 10:
            return False

        # 의미있는 문자 비율 체크
        meaningful_chars = sum(1 for c in text if c.isalnum() or c in '.,!?;:')
        if len(text) > 0 and meaningful_chars / len(text) < 0.1:
            return False

        return True
