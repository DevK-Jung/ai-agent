"""대화 요약 생성 노드"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage
from langchain_openai import ChatOpenAI

from app.agents.state import ChatState
from app.agents.prompts.summary import CONVERSATION_SUMMARY_PROMPT  
from app.core.config import settings


async def summarize_conversation(state: ChatState) -> dict:
    """현재 메시지 히스토리를 요약하고 최근 2개 메시지만 유지"""
    
    messages = state.get("messages", [])
    if len(messages) <= 2:
        return {}
    
    try:
        # 기존 summary가 있는지 확인
        existing_summary = state.get("summary", "")
        
        # 요약할 메시지들 (마지막 2개 제외)
        messages_to_summarize = messages[:-2]
        
        llm = ChatOpenAI(
            model=settings.CONVERSATION_SUMMARY_MODEL,
            temperature=settings.CONVERSATION_SUMMARY_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY
        )
        
        # 요약 프롬프트 준비
        summary_messages = [SystemMessage(content=CONVERSATION_SUMMARY_PROMPT)]
        
        # 기존 summary가 있으면 추가
        if existing_summary:
            summary_messages.append(SystemMessage(content=f"[기존 요약]\n{existing_summary}"))
        
        # 요약할 메시지들 추가
        for msg in messages_to_summarize:
            if hasattr(msg, 'content'):
                if 'Human' in type(msg).__name__:
                    summary_messages.append(HumanMessage(content=msg.content))
                elif 'AI' in type(msg).__name__:
                    summary_messages.append(AIMessage(content=msg.content))
        
        # 요약 생성
        response = await llm.ainvoke(summary_messages)
        new_summary = response.content
        
        # 오래된 메시지들 제거 (RemoveMessage 사용)
        messages_to_remove = []
        for i, msg in enumerate(messages[:-2]):  # 마지막 2개 제외하고 제거
            if hasattr(msg, 'id'):
                messages_to_remove.append(RemoveMessage(id=msg.id))
        
        # 새로운 메시지 리스트 구성: 요약 SystemMessage + 최근 2개 메시지
        summary_message = SystemMessage(content=f"[대화 요약]\n{new_summary}")
        new_messages = [summary_message] + messages[-2:]  # 최근 2개 메시지만 유지
        
        # dict 반환
        return {
            "messages": messages_to_remove + new_messages,  # RemoveMessage들 + 새 메시지들
            "summary": new_summary
        }
        
    except Exception as e:
        print(f"Summarization error: {e}")
        # 에러 발생시에도 기본 요약 메시지 추가
        summary_message = SystemMessage(content="[대화 요약]\n이전 대화가 요약되었습니다.")
        return {
            "messages": [summary_message] + messages[-2:],
            "summary": "이전 대화가 요약되었습니다."
        }