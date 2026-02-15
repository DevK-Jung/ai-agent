from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.workflows.chat_workflow import process_chat, process_chat_stream
from app.core.exceptions import WorkflowException, ValidationException
import json

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
    # 입력 검증
    if not request.message or not request.message.strip():
        raise ValidationException("메시지가 비어있습니다.")
    
    try:
        result = await process_chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        # 커스텀 예외로 래핑하여 예외 핸들러가 처리하도록 함
        raise WorkflowException(
            message="채팅 워크플로우 실행 중 오류가 발생했습니다.",
            details={"original_error": str(e)}
        )


@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    채팅 메시지를 스트리밍으로 처리합니다 (SSE).
    
    - **message**: 사용자의 질문 또는 메시지
    - **user_id**: 선택적 사용자 ID
    - **session_id**: 선택적 세션 ID (없으면 자동 생성)
    """
    async def generate_events():
        try:
            async for chunk in process_chat_stream(
                message=request.message,
                user_id=request.user_id,
                session_id=request.session_id
            ):
                # 청크 타입에 따라 다른 이벤트명 사용
                event_type = chunk.get("type", "message")
                yield {
                    "event": event_type,  # start, progress, chunk, complete, error
                    "data": json.dumps(chunk, ensure_ascii=False)
                }
        except Exception as e:
            # 오류 이벤트 전송
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": True,
                    "message": f"채팅 처리 중 오류가 발생했습니다: {str(e)}"
                }, ensure_ascii=False)
            }
    
    return EventSourceResponse(generate_events())


@router.get("/health")
async def chat_health():
    """채팅 서비스 상태 확인"""
    return {"status": "healthy", "service": "chat"}