# nodes/save_message.py
"""메시지를 DB에 영구 저장하는 노드"""

from langchain_core.messages import HumanMessage, AIMessage

from app.agents.state import ChatState
from app.db.database import AsyncSessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService


async def _save_messages(session_id: str, user_id: str, human_msg, ai_msg) -> None:
    """DB에 메시지 저장"""
    async with AsyncSessionLocal() as db:
        try:
            repo = ConversationRepository(db)
            service = ConversationService(repo)

            thread = await service.get_or_create_thread(session_id, user_id)

            if human_msg:
                await service.save_message(
                    thread_id=thread.thread_id,
                    user_id=user_id,
                    role="human",
                    content=human_msg.content
                )

            if ai_msg:
                await service.save_message(
                    thread_id=thread.thread_id,
                    user_id=user_id,
                    role="assistant",
                    content=ai_msg.content
                )

            await db.commit()

        except Exception as e:
            await db.rollback()
            raise e


async def save_message_to_db(state: ChatState) -> dict:
    """현재 턴의 human + ai 메시지를 DB에 저장"""

    session_id = state.get("session_id")
    user_id = state.get("user_id")
    messages = state.get("messages", [])

    if not session_id or not messages:
        return {}

    # 역순으로 탐색하여 최근 Human-AI 쌍 찾기
    human_msg = None
    ai_msg = None

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and not human_msg:
            human_msg = msg
        elif isinstance(msg, AIMessage) and not ai_msg:
            ai_msg = msg

        if human_msg and ai_msg:
            break

    try:
        await _save_messages(session_id, user_id, human_msg, ai_msg)
        print(f"Saved messages to DB for session: {session_id}")

    except Exception as e:
        print(f"Save message to DB error: {e}")
        # DB 저장 실패해도 워크플로우는 계속 진행

    return {}
