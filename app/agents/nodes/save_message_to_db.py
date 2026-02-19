"""메시지를 DB에 영구 저장하는 노드"""

from app.agents.state import ChatState
from app.db.database import get_database_session
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService


async def save_message_to_db(state: ChatState) -> dict:
    """현재 턴의 human + ai 메시지를 DB에 저장"""
    
    session_id = state.get("session_id")
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    
    if not session_id or not messages:
        return {}
    
    try:
        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            conversation_repo = ConversationRepository(db)
            conversation_service = ConversationService(conversation_repo)
            
            # 스레드 확인/생성
            thread = await conversation_service.get_or_create_thread(session_id, user_id)
            
            # 현재 턴의 메시지들 찾기 (가장 최근 Human + AI 쌍)
            recent_messages = []
            
            # 역순으로 탐색하여 최근 Human-AI 쌍 찾기
            human_msg = None
            ai_msg = None
            
            for msg in reversed(messages):
                if hasattr(msg, 'content'):
                    if 'Human' in type(msg).__name__ and not human_msg:
                        human_msg = msg
                    elif 'AI' in type(msg).__name__ and not ai_msg:
                        ai_msg = msg
                    
                    # Human-AI 쌍이 완성되면 중단
                    if human_msg and ai_msg:
                        break
            
            # 메시지 저장
            if human_msg:
                await conversation_service.save_message(
                    thread_id=thread.thread_id,
                    user_id=user_id,
                    role="human",
                    content=human_msg.content
                )
            
            if ai_msg:
                await conversation_service.save_message(
                    thread_id=thread.thread_id,
                    user_id=user_id,
                    role="assistant", 
                    content=ai_msg.content
                )
                
            await db.commit()
            print(f"Saved messages to DB for session: {session_id}")
            
    except Exception as e:
        await db.rollback()
        print(f"Save message to DB error: {e}")
        # DB 저장 실패해도 워크플로우는 계속 진행
    
    return {}