"""최종 응답 생성 노드 - 모든 에이전트 결과를 통합하여 최종 답변 생성

supervisor가 모든 작업 완료를 판단하면 이 노드로 분기.
named AIMessage(에이전트 결과)를 확인하여:
- 단일 에이전트: 결과 그대로 answer에 저장
- 다중 에이전트: LLM으로 통합한 뒤 answer에 저장
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.core.llm_provider import gpt4o_mini
from app.agents.prompts.router import FINAL_RESPONSE_SYSTEM_PROMPT
from app.agents.state import RouterState


async def final_response_agent_node(state: RouterState) -> dict:
    messages = state.get("messages", [])

    # 에이전트가 남긴 named AIMessage 수집
    agent_results = [m for m in messages if isinstance(m, HumanMessage) and m.name]

    if len(agent_results) == 1:
        # 단일 에이전트: 결과 그대로 반환
        answer = agent_results[0].content
    else:
        # 다중 에이전트: LLM으로 통합
        response = await gpt4o_mini.ainvoke(
            [SystemMessage(content=FINAL_RESPONSE_SYSTEM_PROMPT)] + messages
        )
        answer = response.content

    return {"answer": answer}
