from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.workflows.chat_workflow import process_chat

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    채팅 메시지를 처리하고 AI 응답을 반환합니다.
    
    - **message**: 사용자의 질문 또는 메시지
    - **user_id**: 선택적 사용자 ID
    - **session_id**: 선택적 세션 ID (없으면 자동 생성)
    """
    try:
        result = await process_chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """채팅 서비스 상태 확인"""
    return {"status": "healthy", "service": "chat"}