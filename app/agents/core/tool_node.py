"""공통 Tool Node - 모든 워크플로우에서 공유하는 tool node 유틸"""

from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode


def build_tool_node(tools: list[BaseTool]) -> ToolNode:
    """
    툴 리스트로 ToolNode 생성.

    Args:
        tools: 실행할 툴 리스트

    Returns:
        LangGraph ToolNode 인스턴스

    Example:
        >>> tool_node = build_tool_node([gmail_tool, arxiv_tool])
        >>> workflow.add_node("tools", tool_node)
    """
    return ToolNode(tools)
