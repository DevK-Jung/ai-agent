# infra/vector_db/__init__.py

from .client import VectorDBClient
from .dependencies import VectorDBClientDep, startup_vector_db, shutdown_vector_db

# from .embedding import OllamaEmbeddingService

__all__ = [
    "VectorDBClient",
    "VectorDBClientDep",
    "startup_vector_db",
    "shutdown_vector_db",
    # "OllamaEmbeddingService"
]
