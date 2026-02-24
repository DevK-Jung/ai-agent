"""토큰 카운팅 및 관련 유틸리티 함수들"""

import tiktoken

# GPT-4o 계열 모델용 인코더 (청킹과 메시지 토큰 계산에 일관성 유지)
_encoder = tiktoken.encoding_for_model("gpt-4o-mini")


def count_tokens(text: str) -> int:
    """문자열의 토큰 수를 계산합니다.
    
    Args:
        text: 토큰 수를 계산할 문자열
        
    Returns:
        int: 토큰 수
    """
    try:
        return len(_encoder.encode(text))
    except Exception as e:
        # fallback to approximate counting (1 token ≈ 3 characters for Korean)
        return len(text) // 3


def count_messages_tokens(messages) -> int:
    """메시지 리스트의 총 토큰 수를 계산합니다.
    
    Args:
        messages: 메시지 리스트 (LangChain messages 또는 dict 형태)
        
    Returns:
        int: 총 토큰 수
    """
    try:
        total = 0

        for message in messages:
            if hasattr(message, 'content') and message.content:
                total += count_tokens(str(message.content))
            elif isinstance(message, dict) and 'content' in message:
                total += count_tokens(str(message['content']))

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


def get_tiktoken_encoder():
    """tiktoken 인코더를 반환합니다."""
    return _encoder