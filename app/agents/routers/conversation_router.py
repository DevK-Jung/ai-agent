"""대화 이력 복원이 필요한지 판단하는 라우터"""

from typing import Literal

from app.agents.state import ChatState


def need_prev_conversation(state: ChatState) -> Literal["load_db", "check_token"]:
    """세션 상태에 따른 분기 판단"""

    messages = state.get("messages", [])
    is_new_session = state.get("is_new_session", False)

    # 체크포인터에 이미 대화 이력이 있음
    if len(messages) > 1:
        return "check_token"

    # 새 대화 - DB 조회 불필요
    if is_new_session:
        return "check_token"

    # 기존 session_id인데 체크포인터에 없음 = DB 조회 필요
    return "load_db"
