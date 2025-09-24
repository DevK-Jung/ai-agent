import logging

from .repository import CollectionRepository
from .schemas import CollectionCreateRequest, CollectionResponse

logger = logging.getLogger(__name__)


class CollectionService:
    """컬렉션 서비스 - 비즈니스 로직"""

    def __init__(self, repository: CollectionRepository):
        self.repository = repository

    async def create_collection(self, request: CollectionCreateRequest) -> CollectionResponse:
        """컬렉션 생성"""
        try:

            # 컬렉션 생성
            success = await self.repository.create_collection(request.name)

            return CollectionResponse(
                success=success,
                message="컬렉션이 성공적으로 생성되었습니다" if success else "컬렉션 생성에 실패했습니다",
                collection_name=request.name
            )

        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {e}")
            return CollectionResponse(
                success=False,
                message=f"컬렉션 생성 중 오류가 발생했습니다: {str(e)}",
                collection_name=request.name
            )

    async def delete_collection(self, name: str) -> CollectionResponse:
        """컬렉션 삭제"""
        try:

            # 컬렉션 삭제
            success = await self.repository.delete_collection(name)

            return CollectionResponse(
                success=success,
                message="컬렉션이 성공적으로 삭제되었습니다" if success else "컬렉션 삭제에 실패했습니다",
                collection_name=name
            )

        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {e}")
            return CollectionResponse(
                success=False,
                message=f"컬렉션 삭제 중 오류가 발생했습니다: {str(e)}",
                collection_name=name
            )
