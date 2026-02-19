"""대화 이력 관리 서비스"""

import logging
from typing import List, Optional, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.models.conversation import ConversationMessage, ConversationThread
from app.repositories.conversation_repository import ConversationRepository
from app.core.config import settings


class ConversationService:
    """대화 관리 서비스 - Repository 패턴 적용"""
    
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository
        self.logger = logging.getLogger(__name__)
    
    async def save_message(
        self, 
        thread_id: str, 
        user_id: Optional[str],
        role: str, 
        content: str
    ) -> ConversationMessage:
        """메시지를 데이터베이스에 저장"""
        try:
            message = await self.conversation_repository.save_message(thread_id, user_id, role, content)
            await self.conversation_repository.update_thread_timestamp(thread_id)
            
            self.logger.info(f"메시지 저장 완료: {thread_id}")
            return message
            
        except Exception as e:
            self.logger.error(f"메시지 저장 실패: {e}")
            raise
    
    async def get_thread_messages(
        self, 
        thread_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """스레드의 최근 메시지들을 조회"""
        try:
            messages = await self.conversation_repository.get_thread_messages(thread_id, limit)
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
            
        except Exception as e:
            self.logger.error(f"스레드 메시지 조회 실패: {e}")
            return []
    
    async def get_past_messages_for_summary(
        self, 
        thread_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """요약용 이전 대화 기록 조회"""
        try:
            messages = await self.conversation_repository.get_thread_messages(thread_id, limit)
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
            
        except Exception as e:
            self.logger.error(f"과거 메시지 조회 실패: {e}")
            return []
    
    async def get_or_create_thread(
        self, 
        thread_id: str, 
        user_id: Optional[str],
        title: Optional[str] = None
    ) -> ConversationThread:
        """스레드 조회 또는 생성"""
        try:
            thread = await self.conversation_repository.get_thread_by_id(thread_id)
            
            if not thread:
                thread = await self.conversation_repository.create_thread(thread_id, user_id, title)
                self.logger.info(f"새 스레드 생성 완료: {thread_id}")
            
            return thread
            
        except Exception as e:
            self.logger.error(f"스레드 조회/생성 실패: {e}")
            raise
    
    async def get_user_threads(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[ConversationThread]:
        """사용자의 대화 스레드 목록 조회"""
        try:
            return await self.conversation_repository.get_user_threads(user_id, limit)
            
        except Exception as e:
            self.logger.error(f"사용자 스레드 조회 실패: {e}")
            return []