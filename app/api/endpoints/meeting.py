"""회의록 관련 API 엔드포인트"""

import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json

from app.agents.workflows.meeting_workflow import process_meeting, process_meeting_stream

router = APIRouter(prefix="/meeting", tags=["meeting"])


@router.post("/upload")
async def upload_audio_and_generate_minutes(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    오디오 파일을 업로드하고 회의록을 생성합니다.
    
    Args:
        file: 업로드할 오디오 파일
        user_id: 사용자 ID (선택사항)
        session_id: 세션 ID (선택사항)
        
    Returns:
        생성된 회의록과 관련 메타데이터
    """
    # 파일 형식 검증
    allowed_formats = [
        "audio/wav", "audio/mp3", "audio/m4a", "audio/flac", 
        "audio/ogg", "audio/mpeg", "audio/mp4", "audio/x-m4a"
    ]
    
    if file.content_type not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_formats)}"
        )
    
    # 파일 크기 제한 (100MB)
    max_file_size = 100 * 1024 * 1024
    file_size = 0
    
    try:
        # 임시 파일 저장
        upload_dir = "data/temp_audio"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192)  # 8KB씩 읽기
                if not chunk:
                    break
                file_size += len(chunk)
                
                if file_size > max_file_size:
                    os.remove(file_path) if os.path.exists(file_path) else None
                    raise HTTPException(
                        status_code=413,
                        detail="파일 크기가 너무 큽니다. 최대 100MB까지 지원됩니다."
                    )
                
                buffer.write(chunk)
        
        # 회의록 생성 처리
        result = await process_meeting(
            audio_file_path=file_path,
            user_id=user_id,
            session_id=session_id
        )
        
        # 임시 파일 삭제
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"회의록 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/upload/stream")
async def upload_audio_and_stream_minutes(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None), 
    session_id: Optional[str] = Form(None)
):
    """
    오디오 파일을 업로드하고 회의록을 스트리밍으로 생성합니다.
    
    Args:
        file: 업로드할 오디오 파일
        user_id: 사용자 ID (선택사항)
        session_id: 세션 ID (선택사항)
        
    Returns:
        SSE 스트리밍 응답
    """
    # 파일 형식 검증
    allowed_formats = [
        "audio/wav", "audio/mp3", "audio/m4a", "audio/flac",
        "audio/ogg", "audio/mpeg", "audio/mp4", "audio/x-m4a"
    ]
    
    if file.content_type not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_formats)}"
        )
    
    # 파일 크기 제한 (100MB) 
    max_file_size = 100 * 1024 * 1024
    file_size = 0
    
    try:
        # 임시 파일 저장
        upload_dir = "data/temp_audio"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                file_size += len(chunk)
                
                if file_size > max_file_size:
                    os.remove(file_path) if os.path.exists(file_path) else None
                    raise HTTPException(
                        status_code=413,
                        detail="파일 크기가 너무 큽니다. 최대 100MB까지 지원됩니다."
                    )
                
                buffer.write(chunk)
        
        async def event_generator():
            try:
                async for event_data in process_meeting_stream(
                    audio_file_path=file_path,
                    user_id=user_id,
                    session_id=session_id
                ):
                    yield {
                        "event": "message",
                        "data": json.dumps(event_data, ensure_ascii=False)
                    }
            finally:
                # 스트리밍 완료 후 임시 파일 삭제
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        
        return EventSourceResponse(event_generator())
        
    except HTTPException:
        raise
    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"회의록 생성 중 오류가 발생했습니다: {str(e)}"
        )