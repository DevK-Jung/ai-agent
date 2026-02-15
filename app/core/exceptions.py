"""커스텀 예외 클래스들"""
from typing import Any, Dict, Optional


class AIAgentException(Exception):
    """기본 AI Agent 예외"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class WorkflowException(AIAgentException):
    """워크플로우 실행 중 발생하는 예외"""
    pass


class LLMException(AIAgentException):
    """LLM 호출 중 발생하는 예외"""
    pass


class DocumentProcessingException(AIAgentException):
    """문서 처리 중 발생하는 예외"""
    pass


class DatabaseException(AIAgentException):
    """데이터베이스 관련 예외"""
    pass


class ValidationException(AIAgentException):
    """입력 검증 실패 예외"""
    pass