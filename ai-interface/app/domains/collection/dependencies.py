from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from .repository import CollectionRepository
from .service import CollectionService
from ...infra.vector_db.connection import PostgresConnectionManager


def get_collection_repository(
        settings: SettingsDep,
) -> CollectionRepository:
    return CollectionRepository(settings, PostgresConnectionManager(settings))


def get_collection_service(
        repository: Annotated[CollectionRepository, Depends(get_collection_repository)],
) -> CollectionService:
    return CollectionService(repository)


CollectionServiceDep = Annotated[CollectionService, Depends(get_collection_service)]
