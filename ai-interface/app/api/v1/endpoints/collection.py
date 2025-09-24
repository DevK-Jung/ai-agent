# app/api/v1/endpoints/collection.py
import logging
from typing import List

from fastapi import APIRouter, Path

from app.domains.collection.dependencies import CollectionServiceDep
from app.domains.collection.schemas import (
    CollectionCreateRequest,
    CollectionResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[str])
async def list_collection(collection_service: CollectionServiceDep):
    return await collection_service.list_collection()


@router.post("/", response_model=CollectionResponse)
async def create_collection(
        collection_service: CollectionServiceDep,
        request: CollectionCreateRequest
):
    """컬렉션 생성"""
    return await collection_service.create_collection(request)


@router.delete("/{collection_name}", response_model=CollectionResponse)
async def delete_collection(
        collection_service: CollectionServiceDep,
        collection_name: str = Path(..., description="컬렉션 이름")
):
    """컬렉션 삭제"""
    return await collection_service.delete_collection(collection_name)
