from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.infra.vector_db.dependencies import VectorDBClientDep
from .repository import DocumentRepository
from .service import DocumentService


def get_document_repository(
        vector_db_client: VectorDBClientDep
) -> DocumentRepository:
    return DocumentRepository(vector_db_client)


def get_document_service(
        repository: Annotated[DocumentRepository, Depends(get_document_repository)],
        settings: SettingsDep
) -> DocumentService:
    return DocumentService(repository, settings)


DocumentRepositoryDep = Annotated[DocumentRepository, Depends(get_document_repository)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]