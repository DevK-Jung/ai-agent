# nodes/load_history.py
"""DB에서 이전 대화 기록을 로드하는 노드"""

from langchain_core.messages import HumanMessage, AIMessage

from app.agents.state import ChatState
from app.db.database import AsyncSessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService


async def load_history_from_db(state: ChatState) -> dict:
    """DB에서 이전 대화 기록을 조회해서 messages에 추가"""

    session_id = state.get("session_id")
    user_id = state.get("user_id")

    if not session_id:
        return {}

    try:
        past_messages = await _get_history(session_id, user_id)

        if not past_messages:
            return {}

        history_messages = [
            HumanMessage(content=msg["content"]) if msg["role"] == "human"
            else AIMessage(content=msg["content"])
            for msg in past_messages
        ]

        current_messages = state.get("messages", [])
        return {"messages": history_messages + current_messages}

    except Exception as e:
        print(f"History load error: {e}")
        return {}


async def _get_history(session_id: str, user_id: str) -> list:
    """DB에서 이전 대화 기록 조회"""
    async with AsyncSessionLocal() as db:
        try:
            repo = ConversationRepository(db)
            service = ConversationService(repo)

            await service.get_or_create_thread(session_id, user_id)
            messages = await service.get_recent_messages(session_id, limit=20)

            await db.commit()
            return messages

        except Exception as e:
            await db.rollback()
            print(f"DB error: {e}")
            return []
