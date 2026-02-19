"""PostgreSQL checkpointer 설정 및 관리"""
import logging
from typing import AsyncContextManager, Optional, Dict, Any, List

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import settings

logger = logging.getLogger(__name__)


async def get_postgres_checkpointer() -> AsyncContextManager[AsyncPostgresSaver]:
    """PostgreSQL checkpointer 컨텍스트 매니저를 반환합니다."""
    try:
        conn_string = settings.CHECKPOINTER_CONNECTION_STRING

        # checkpointer 생성
        checkpointer_context = AsyncPostgresSaver.from_conn_string(
            conn_string,
        )
        return checkpointer_context
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL checkpointer: {e}")
        raise


async def setup_checkpointer_tables() -> None:
    """체크포인터 테이블을 안전하게 초기화합니다."""
    try:
        async with await get_postgres_checkpointer() as checkpointer:
            await checkpointer.setup()
            logger.info(f"Checkpointer tables setup completed")
    except Exception as e:
        logger.error(f"Failed to setup checkpointer tables: {e}")
        raise


async def get_checkpointer_stats(
        thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """체크포인터 통계 정보를 반환합니다."""
    try:
        async with await get_postgres_checkpointer() as checkpointer:
            config = {"configurable": {"thread_id": thread_id}} if thread_id else {}

            # 체크포인트 목록 조회
            checkpoints = []
            async for checkpoint in checkpointer.alist(config, limit=100):
                checkpoints.append(checkpoint)

            if not checkpoints:
                return {
                    "total_checkpoints": 0,
                    "thread_id": thread_id,
                    "oldest_checkpoint": None,
                    "newest_checkpoint": None,
                    "total_messages": 0
                }

            # 통계 계산
            total_messages = 0
            for cp in checkpoints:
                messages = cp.checkpoint.get('channel_values', {}).get('messages', [])
                total_messages += len(messages)

            stats = {
                "total_checkpoints": len(checkpoints),
                "thread_id": thread_id,
                "oldest_checkpoint": checkpoints[-1].config if checkpoints else None,
                "newest_checkpoint": checkpoints[0].config if checkpoints else None,
                "total_messages": total_messages,
                "avg_messages_per_checkpoint": total_messages / len(checkpoints) if checkpoints else 0
            }

            logger.debug(f"Checkpointer stats collected: {stats}")
            return stats

    except Exception as e:
        logger.error(f"Failed to get checkpointer stats: {e}")
        return {"error": str(e)}


async def get_thread_messages(
        thread_id: str,
        limit: int = 50
) -> List[Dict[str, Any]]:
    """특정 스레드의 메시지 히스토리를 반환합니다."""
    try:
        async with await get_postgres_checkpointer() as checkpointer:
            config = {"configurable": {"thread_id": thread_id}}

            # 최신 체크포인트 조회
            latest_checkpoint = None
            async for checkpoint in checkpointer.alist(config, limit=1):
                latest_checkpoint = checkpoint
                break

            if not latest_checkpoint:
                return []

            # 메시지 추출 및 변환
            messages = latest_checkpoint.checkpoint.get('channel_values', {}).get('messages', [])
            result = []

            for msg in messages[-limit:]:  # 최근 N개만
                if hasattr(msg, 'content'):
                    msg_type = 'user' if 'Human' in type(msg).__name__ else 'assistant'
                    result.append({
                        "type": msg_type,
                        "content": msg.content,
                        "timestamp": getattr(msg, 'timestamp', None)
                    })
                elif isinstance(msg, dict):
                    result.append(msg)

            logger.debug(f"Retrieved {len(result)} messages for thread {thread_id}")
            return result

    except Exception as e:
        logger.error(f"Failed to get thread messages: {e}")
        return []
