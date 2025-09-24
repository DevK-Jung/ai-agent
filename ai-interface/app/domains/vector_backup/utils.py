from typing import Optional

from .constants import DocumentType
from .schemas import SearchRequest, DocumentRequest


def create_search_request(
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None,
        **kwargs
) -> SearchRequest:
    """검색 요청 생성 헬퍼 함수"""
    return SearchRequest(
        query=query,
        k=k,
        collection_name=collection_name,
        **kwargs
    )


def create_document_request(
        content: str,
        document_type: DocumentType = DocumentType.TEXT,
        **kwargs
) -> DocumentRequest:
    """문서 요청 생성 헬퍼 함수"""
    return DocumentRequest(
        content=content,
        document_type=document_type,
        **kwargs
    )
