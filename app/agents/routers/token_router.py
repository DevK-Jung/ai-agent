"""토큰 수를 확인하여 요약 필요성을 판단하는 라우터"""

import tiktoken
from typing import Literal
from app.agents.state import ChatState


def count_tokens(messages, model="gpt-4o-mini") -> int:
    """tiktoken을 사용한 정확한 토큰 수 계산"""
    try:
        enc = tiktoken.encoding_for_model(model)
        total = 0
        
        for message in messages:
            if hasattr(message, 'content') and message.content:
                total += len(enc.encode(str(message.content)))
            elif isinstance(message, dict) and 'content' in message:
                total += len(enc.encode(str(message['content'])))
        
        return total
    except Exception as e:
        print(f"Token counting error: {e}")
        # fallback to approximate counting
        total_chars = 0
        for message in messages:
            if hasattr(message, 'content'):
                total_chars += len(str(message.content))
            elif isinstance(message, dict) and 'content' in message:
                total_chars += len(str(message['content']))
        return total_chars // 3


def check_token_count(state: ChatState) -> Literal["summarize", "classify"]:
    """현재 메시지 토큰 수가 8000을 초과하는지 확인"""
    
    messages = state.get("messages", [])
    if not messages:
        return "classify"
    
    try:
        token_count = count_tokens(messages)
        
        # 8000 토큰 초과시 요약 필요
        if token_count > 8000:
            return "summarize"
        else:
            return "classify"
            
    except Exception as e:
        print(f"Token count error: {e}")
        # 에러 발생시 안전하게 분류로 진행
        return "classify"