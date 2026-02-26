from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool


@tool
def duckduckgo_tool(query: str, max_results: int = 5) -> str:
    """
    DuckDuckGo로 웹을 검색합니다.

    Args:
        query: 검색 쿼리
        max_results: 최대 검색 결과 수 (기본값: 5)
    """
    search = DuckDuckGoSearchResults(num_results=max_results)
    return search.run(query)
