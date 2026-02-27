"""대화 요약 노드 - 토큰 예산(30%) 내에서 최근 메시지 최대 보존 후 나머지 요약

토큰 초과 여부는 token_router edge에서 판단하므로 이 노드는 항상 요약을 실행.
"""

from langchain_core.messages import RemoveMessage, SystemMessage

from app.agents.core.llm_provider import gpt4o, gpt4o_mini
from app.agents.prompts.router import SUMMARIZE_PROMPT
from app.agents.state import RouterState
from app.core.config import settings

_summarize_chain = SUMMARIZE_PROMPT | gpt4o_mini.bind(max_tokens=settings.SUMMARIZE_MAX_SUMMARY_TOKENS)


async def summarize_node(state: RouterState) -> dict:
    messages = state.get("messages", [])

    # 토큰 예산의 30%를 최근 메시지 보존에 사용
    recent_budget = int(settings.SUMMARIZE_MAX_TOKENS * 0.3)

    # 뒤에서부터 예산 내 최대한 메시지 유지
    kept = []
    used_tokens = 0
    for m in reversed(messages):
        msg_tokens = gpt4o.get_num_tokens_from_messages([m])
        if used_tokens + msg_tokens <= recent_budget:
            kept.insert(0, m)
            used_tokens += msg_tokens
        else:
            break

    kept_ids = {id(m) for m in kept}
    messages_to_summarize = [m for m in messages if id(m) not in kept_ids]

    if not messages_to_summarize:
        return {}

    try:
        summary_response = await _summarize_chain.ainvoke({"messages": messages_to_summarize})
        summary_text = summary_response.content.strip()
    except Exception as e:
        print(f"Summarization error: {e}")
        return {}  # 요약 실패 시 원본 유지

    delete_old = [RemoveMessage(id=m.id) for m in messages_to_summarize if m.id]

    return {
        "messages": [
            *delete_old,
            SystemMessage(f"[이전 대화 요약]\n{summary_text}"),
            *kept,
        ]
    }