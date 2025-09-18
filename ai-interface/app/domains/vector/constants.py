from enum import Enum


class ChunkingStrategy(str, Enum):
    """텍스트 분할 전략"""
    RECURSIVE_CHARACTER = "recursive_character"
    TOKEN_BASED = "token_based"
    SEMANTIC = "semantic"


class DocumentType(str, Enum):
    """문서 타입"""
    TEXT = "text"
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE = "code"


class SearchType(str, Enum):
    """검색 타입"""
    SIMILARITY = "similarity"
    MMR = "mmr"  # Maximum Marginal Relevance
    VECTOR = "vector"