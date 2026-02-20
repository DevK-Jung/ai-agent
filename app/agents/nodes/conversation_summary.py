# nodes/conversation_summary.py
"""대화 요약 생성 노드"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage
from langchain_openai import ChatOpenAI

from app.agents.prompts.summary import CONVERSATION_SUMMARY_PROMPT
from app.agents.state import ChatState
from app.core.config import settings


_summary_llm = ChatOpenAI(
    model=settings.CONVERSATION_SUMMARY_MODEL,
    temperature=settings.CONVERSATION_SUMMARY_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY,
    max_tokens=200
)

_summary_chain = CONVERSATION_SUMMARY_PROMPT | _summary_llm


async def summarize_conversation(state: ChatState) -> dict:
    """현재 메시지 히스토리를 요약하고 최근 2개 메시지만 유지"""

    messages = state.get("messages", [])
    if len(messages) <= 2:
        return {}

    try:
        existing_summary = state.get("summary", "")
        messages_to_summarize = messages[:-2]

        conversation_text = "\n".join([
            f"{'사용자' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
            for msg in messages_to_summarize
            if isinstance(msg, (HumanMessage, AIMessage))
        ])

        existing_section = (
            f"기존 요약을 참고하여 업데이트해주세요:\n{existing_summary}"
            if existing_summary else ""
        )

        response = await _summary_chain.ainvoke({
            "existing_summary": existing_section,
            "conversation": conversation_text
        })
        new_summary = response.content

        messages_to_remove = [
            RemoveMessage(id=msg.id)
            for msg in messages[:-2]
            if getattr(msg, 'id', None) is not None
        ]

        summary_message = SystemMessage(content=f"[대화 요약]\n{new_summary}")

        return {
            "messages": messages_to_remove + [summary_message],
            "summary": new_summary
        }

    except Exception as e:
        print(f"Summarization error: {e}")

        messages_to_remove = [
            RemoveMessage(id=msg.id)
            for msg in messages[:-2]
            if getattr(msg, 'id', None) is not None
        ]
        summary_message = SystemMessage(content="[대화 요약]\n이전 대화가 요약되었습니다.")

        return {
            "messages": messages_to_remove + [summary_message],
            "summary": "이전 대화가 요약되었습니다."
        }