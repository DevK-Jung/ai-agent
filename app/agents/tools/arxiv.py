"""Arxiv 논문 검색 Tool"""
from langchain_community.utilities import ArxivAPIWrapper
from langchain_core.tools import tool


@tool
def arxiv_tool(query: str, max_results: int = 3) -> str:
    """
    Arxiv에서 논문을 검색합니다.

    Args:
        query: 검색 쿼리 (영어 권장)
        max_results: 최대 검색 결과 수 (기본값: 3)

    Returns:
        검색된 논문 목록 (제목, 저자, 요약 포함)
    """
    try:
        arxiv = ArxivAPIWrapper(top_k_results=max_results)
        results = arxiv.run(query)
        return results
    except Exception as e:
        return f"Arxiv 검색 실패: {str(e)}"
