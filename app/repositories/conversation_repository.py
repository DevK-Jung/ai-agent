"""
대화 Repository

대화 스레드 및 메시지 관련 데이터 액세스 로직
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.conversation import ConversationMessage, ConversationThread


class ConversationRepository:
    """대화 관련 데이터 액세스 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
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
            message = ConversationMessage(
                user_id=user_id,
                thread_id=thread_id,
                role=role,
                content=content
            )
            
            self.db.add(message)
            await self.db.flush()
            
            self.logger.debug(f"메시지 저장 완료: {thread_id}")
            return message
            
        except Exception as e:
            self.logger.error(f"메시지 저장 실패: {e}")
            raise
    
    async def get_thread_messages(
        self, 
        thread_id: str, 
        limit: int = 20
    ) -> List[ConversationMessage]:
        """스레드의 최근 메시지들을 조회"""
        try:
            query = (
                select(ConversationMessage)
                .where(ConversationMessage.thread_id == thread_id)
                .order_by(desc(ConversationMessage.created_at))
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            self.logger.debug(f"스레드 메시지 조회 완료: {len(messages)}개")
            return list(reversed(messages))  # 시간순 정렬
            
        except Exception as e:
            self.logger.error(f"스레드 메시지 조회 실패: {e}")
            return []
    
    async def create_thread(
        self, 
        thread_id: str, 
        user_id: Optional[str],
        title: Optional[str] = None
    ) -> ConversationThread:
        """새 대화 스레드 생성"""
        try:
            thread = ConversationThread(
                thread_id=thread_id,
                user_id=user_id,
                title=title or "새 대화"
            )
            
            self.db.add(thread)
            await self.db.flush()
            
            self.logger.debug(f"스레드 생성 완료: {thread_id}")
            return thread
            
        except Exception as e:
            self.logger.error(f"스레드 생성 실패: {e}")
            raise
    
    async def get_thread_by_id(self, thread_id: str) -> Optional[ConversationThread]:
        """스레드 ID로 스레드 조회"""
        try:
            query = select(ConversationThread).where(
                ConversationThread.thread_id == thread_id
            )
            
            result = await self.db.execute(query)
            thread = result.scalar_one_or_none()
            
            if thread:
                self.logger.debug(f"스레드 조회 완료: {thread_id}")
            
            return thread
            
        except Exception as e:
            self.logger.error(f"스레드 조회 실패: {e}")
            return None
    
    async def get_user_threads(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[ConversationThread]:
        """사용자의 대화 스레드 목록 조회"""
        try:
            query = (
                select(ConversationThread)
                .where(ConversationThread.user_id == user_id)
                .order_by(desc(ConversationThread.updated_at))
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            threads = result.scalars().all()
            
            self.logger.debug(f"사용자 스레드 조회 완료: {len(threads)}개")
            return list(threads)
            
        except Exception as e:
            self.logger.error(f"사용자 스레드 조회 실패: {e}")
            return []
    
    async def update_thread_timestamp(self, thread_id: str) -> bool:
        """스레드 업데이트 시간 갱신"""
        try:
            thread = await self.get_thread_by_id(thread_id)
            if thread:
                thread.updated_at = func.now()
                await self.db.flush()
                self.logger.debug(f"스레드 타임스탬프 업데이트: {thread_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"스레드 타임스탬프 업데이트 실패: {e}")
            return False