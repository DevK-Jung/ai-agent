from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    question_type: Optional[str] = None
    model_used: str = "gpt-4o-mini"


class ChatHistory(BaseModel):
    user_message: str
    assistant_message: str
    timestamp: str