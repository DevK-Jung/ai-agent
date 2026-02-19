"""DB에서 이전 대화 기록을 로드하는 노드"""

from langchain_core.messages import HumanMessage, AIMessage

from app.agents.state import ChatState
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService


async def load_history_from_db(state: ChatState) -> dict:
    """DB에서 이전 대화 기록을 조회해서 messages에 추가"""
    
    session_id = state.get("session_id")
    user_id = state.get("user_id")
    
    if not session_id:
        return {}
    
    try:
        # DB에서 이전 대화 기록 조회
        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                conversation_repo = ConversationRepository(db)
                conversation_service = ConversationService(conversation_repo)
                
                # 스레드 확인/생성
                await conversation_service.get_or_create_thread(session_id, user_id)
                
                # 최근 20개 메시지 조회
                past_messages = await conversation_service.get_past_messages_for_summary(session_id, limit=20)
                
                await db.commit()
                
                if not past_messages:
                    return {}
                
                # 이전 메시지들을 LangChain 메시지로 변환
                history_messages = []
                for msg_data in past_messages:
                    if msg_data["role"] == "human":
                        history_messages.append(HumanMessage(content=msg_data["content"]))
                    else:
                        history_messages.append(AIMessage(content=msg_data["content"]))
                
                # 현재 메시지 앞에 이전 메시지들 추가
                current_messages = state.get("messages", [])
                return {"messages": history_messages + current_messages}
                
            except Exception as db_error:
                await db.rollback()
                print(f"DB error: {db_error}")
                return {}
            
    except Exception as e:
        print(f"History load error: {e}")
    
    return {}