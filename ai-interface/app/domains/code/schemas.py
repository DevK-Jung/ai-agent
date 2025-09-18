from typing import Optional, Dict, Any

from pydantic import BaseModel


class CodeRequest(BaseModel):
    query: str
    context: Optional[str] = None
    modify_existing: bool = False


class CodeResponse(BaseModel):
    generated_code: str
    explanation: str
    execution_result: Optional[Dict[str, Any]] = None


class ExecuteRequest(BaseModel):
    code: str
    input_data: Optional[Dict[str, Any]] = None
