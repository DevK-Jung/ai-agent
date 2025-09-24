from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.core.database.dependencies import VectorConnectionManagerDep
from app.domains.vector.repository import VectorRepository
from app.domains.vector.service import VectorService


def get_vector_repository(
        connection_manager: VectorConnectionManagerDep
) -> VectorRepository:
    return VectorRepository(connection_manager)


def get_vector_service(
        repository: Annotated[VectorRepository, Depends(get_vector_repository)],
        settings: SettingsDep
) -> VectorService:
    return VectorService(repository, settings)


VectorRepositoryDep = Annotated[VectorRepository, Depends(get_vector_repository)]
VectorServiceDep = Annotated[VectorService, Depends(get_vector_service)]