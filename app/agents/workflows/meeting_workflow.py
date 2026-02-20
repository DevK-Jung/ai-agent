"""회의록 처리 워크플로우"""

import uuid
from typing import AsyncGenerator, Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.nodes.meeting import transcribe_audio, merge_transcript, generate_minutes
from app.agents.state import MeetingState


async def create_meeting_workflow():
    """회의록 처리 워크플로우 생성"""

    workflow = StateGraph(MeetingState)

    # 노드 추가
    workflow.add_node("transcribe", transcribe_audio)
    workflow.add_node("merge", merge_transcript)
    workflow.add_node("generate", generate_minutes)

    # 워크플로우 연결
    workflow.set_entry_point("transcribe")
    workflow.add_edge("transcribe", "merge")
    workflow.add_edge("merge", "generate")
    workflow.add_edge("generate", END)

    return workflow


async def process_meeting(
        audio_file_path: str,
        user_id: str | None = None,
        session_id: str | None = None,
) -> dict:
    """
    회의 오디오 파일을 처리하여 회의록을 생성합니다.
    
    Args:
        audio_file_path: 처리할 오디오 파일 경로
        user_id: 사용자 ID
        session_id: 세션 ID
        
    Returns:
        Dict containing meeting minutes and metadata
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    workflow = await create_meeting_workflow()
    app = workflow.compile()

    try:
        final_state = await app.ainvoke({
            "audio_file_path": audio_file_path,
            "session_id": session_id,
            "user_id": user_id or "",
            "transcript": [],
            "merged_transcript": "",
            "minutes": ""
        })

        return {
            "minutes": final_state.get("minutes"),
            "transcript": final_state.get("transcript"),
            "merged_transcript": final_state.get("merged_transcript"),
            "session_id": session_id,
            "audio_file_path": audio_file_path
        }

    except Exception as e:
        print(f"Meeting workflow error: {e}")
        return {
            "minutes": f"회의록 생성 중 오류가 발생했습니다: {str(e)}",
            "transcript": [],
            "merged_transcript": "",
            "session_id": session_id,
            "audio_file_path": audio_file_path
        }


async def process_meeting_stream(
        audio_file_path: str,
        user_id: str | None = None,
        session_id: str | None = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    회의 오디오 파일을 스트리밍으로 처리합니다.
    
    Args:
        audio_file_path: 처리할 오디오 파일 경로
        user_id: 사용자 ID
        session_id: 세션 ID
        
    Yields:
        Dict containing progress updates and final results
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    yield {
        "type": "start",
        "session_id": session_id,
        "message": "음성 파일 전사를 시작합니다..."
    }

    try:
        workflow = await create_meeting_workflow()
        app = workflow.compile()

        async for event in app.astream_events({
            "audio_file_path": audio_file_path,
            "session_id": session_id,
            "user_id": user_id or "",
            "transcript": [],
            "merged_transcript": "",
            "minutes": ""
        }, version="v2"):

            event_type = event["event"]
            event_name = event.get("name", "")
            event_data = event.get("data", {})
            tags = event.get("tags", [])

            # 노드 완료 이벤트 처리 
            if event_type == "on_chain_end" and event_name == "transcribe":
                output = event_data.get("output", {})
                transcript_data = output.get("transcript", [])

                # 전사 결과 요약 생성 (처음 몇 개 세그먼트만 미리보기로)
                preview_segments = transcript_data[:3] if transcript_data else []
                transcript_preview = []

                for segment in preview_segments:
                    speaker = segment.get("speaker", "SPEAKER_00")
                    text = segment.get("text", "").strip()
                    start_time = segment.get("start", 0)
                    transcript_preview.append(f"{speaker} ({start_time:.1f}s): {text}")

                yield {
                    "type": "progress",
                    "step": "transcribe",
                    "message": "음성 전사 및 화자 분리가 완료되었습니다...",
                    "transcript_preview": transcript_preview,
                    "total_segments": len(transcript_data),
                    "speakers": list(set(seg.get("speaker", "SPEAKER_00") for seg in transcript_data))
                }

            elif event_type == "on_chain_end" and event_name == "merge":
                output = event_data.get("output", {})
                merged_text = output.get("merged_transcript", "")
                preview_text = merged_text[:200] + "..." if len(merged_text) > 200 else merged_text

                yield {
                    "type": "progress",
                    "step": "merge",
                    "message": "전사 내용을 정리하고 있습니다...",
                    "merged_preview": preview_text,
                    "total_length": len(merged_text)
                }

            # 회의록 생성 시작
            elif event_type == "on_chain_start" and event_name == "generate":
                yield {
                    "type": "progress",
                    "step": "generate_start",
                    "message": "회의록을 생성하고 있습니다..."
                }

            # LLM 스트리밍 토큰 처리
            elif event_type == "on_chat_model_stream" and "STREAM_MEETING_GENERATOR" in tags:
                chunk = event_data.get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    yield {
                        "type": "chunk",
                        "chunk": chunk.content,
                        "session_id": session_id,
                        "step": "generate"
                    }

            elif event_type == "on_chain_end" and event_name == "generate":
                output = event_data.get("output", {})
                yield {
                    "type": "complete",
                    "step": "generate",
                    "minutes": output.get("minutes"),
                    "transcript": output.get("transcript"),
                    "merged_transcript": output.get("merged_transcript"),
                    "session_id": session_id,
                    "message": "회의록 생성이 완료되었습니다!"
                }

    except Exception as e:
        yield {
            "type": "error",
            "session_id": session_id,
            "error": str(e),
            "message": f"회의록 생성 중 오류가 발생했습니다: {str(e)}"
        }
