# from typing import List
# from langchain_ollama import OllamaEmbeddings
#
#
# class OllamaEmbeddingService:
#     """Ollama 기반 임베딩 서비스"""
#
#     def __init__(self, model_name: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
#         self.embeddings = OllamaEmbeddings(
#             model=model_name,
#             base_url=base_url
#         )
#
#     def embed_documents(self, documents: List[str]) -> List[List[float]]:
#         return self.embeddings.embed_documents(documents)
#
#     def embed_query(self, query: str) -> List[float]:
#         return self.embeddings.embed_query(query)