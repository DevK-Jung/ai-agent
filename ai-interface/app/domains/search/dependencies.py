from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.infra.vector_db.dependencies import VectorDBClientDep
from .repository import SearchRepository
from .service import SearchService


def get_search_repository(
        vector_db_client: VectorDBClientDep
) -> SearchRepository:
    return SearchRepository(vector_db_client)


def get_search_service(
        repository: Annotated[SearchRepository, Depends(get_search_repository)],
        settings: SettingsDep
) -> SearchService:
    return SearchService(repository, settings)


SearchRepositoryDep = Annotated[SearchRepository, Depends(get_search_repository)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]