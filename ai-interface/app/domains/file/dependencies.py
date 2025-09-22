from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.domains.file.service import FileService


def get_file_service(
        settings: SettingsDep
) -> FileService:
    return FileService(settings)


FileServiceDep = Annotated[FileService, Depends(get_file_service)]
