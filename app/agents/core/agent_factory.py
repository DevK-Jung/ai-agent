"""공통 Agent 팩토리 - 여러 워크플로우에서 재사용 가능한 agent 생성"""

from typing import Callable

from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.agents.core.tool_node import build_tool_node


def build_agent(
        tools: list[BaseTool],
        system_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0,
) -> Callable:
    """
    범용 Agent 생성 팩토리.

    Args:
        tools: 바인딩할 툴 리스트
        system_prompt: 시스템 프롬프트
        model: 사용할 LLM 모델
        temperature: LLM temperature

    Returns:
        LangGraph 노드로 사용 가능한 agent 함수

    Example:
        >>> agent = build_agent(
        ...     tools=[gmail_tool, arxiv_tool],
        ...     system_prompt="논문을 검색하고 요약합니다."
        ... )
        >>> workflow.add_node("agent", agent)
    """
    llm = ChatOpenAI(model=model, temperature=temperature)
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: dict) -> dict:
        """
        State의 messages를 읽어 LLM이 tool 호출 여부를 판단합니다.

        - tool 호출 필요 → tool_calls 포함한 AIMessage 반환
        - tool 호출 불필요 → 일반 텍스트 AIMessage 반환
        """
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    return agent


def create_tool_node_with_fallback(tools: list[BaseTool]) -> Callable:
    """
    에러 핸들링이 포함된 tool node 생성.
    tool 실행 중 에러 발생 시 에러 메시지를 반환합니다.

    Args:
        tools: 실행할 툴 리스트

    Returns:
        LangGraph 노드로 사용 가능한 tool_node 함수
    """
    from langchain_core.messages import ToolMessage

    tool_node = build_tool_node(tools)

    def tool_node_with_fallback(state: dict) -> dict:
        try:
            return tool_node.invoke(state)
        except Exception as e:
            last_message = state["messages"][-1]
            tool_call_id = last_message.tool_calls[0]["id"] if last_message.tool_calls else "unknown"
            error_message = ToolMessage(
                content=f"Tool 실행 중 오류가 발생했습니다: {str(e)}",
                tool_call_id=tool_call_id,
            )
            return {"messages": [error_message]}

    return tool_node_with_fallback
