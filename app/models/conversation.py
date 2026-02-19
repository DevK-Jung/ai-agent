"""대화 관련 데이터베이스 모델"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, func
from app.db.database import Base


class ConversationMessage(Base):
    """대화 메시지 저장 테이블"""
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Text, nullable=True)
    thread_id = Column(Text, nullable=False, index=True)
    role = Column(Text, nullable=False)  # 'human' | 'ai'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())


class ConversationThread(Base):
    """대화 스레드 관리 테이블"""
    __tablename__ = "conversation_threads"

    thread_id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())