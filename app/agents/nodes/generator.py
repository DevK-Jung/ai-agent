from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.agents.state import ChatState
from app.agents.prompts.generation import (
    TYPE_INSTRUCTIONS,
    ANSWER_GENERATION_PROMPT,
    DEFAULT_INSTRUCTION,
    ERROR_MESSAGE
)


def generate_answer(state: ChatState) -> ChatState:
    """답변을 생성하는 노드"""
    
    llm = ChatOpenAI(
        model=settings.GENERATOR_MODEL,
        temperature=settings.GENERATOR_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY
    )
    
    question_type = state.get("question_type", "FACT")
    instruction = TYPE_INSTRUCTIONS.get(question_type, DEFAULT_INSTRUCTION)
    
    answer_prompt = ANSWER_GENERATION_PROMPT.format(
        question_type=question_type,
        instruction=instruction,
        user_message=state["user_message"]
    )
    
    try:
        response = llm.invoke(answer_prompt)
        answer = response.content.strip()
    except Exception as e:
        print(f"Answer generation error: {e}")
        answer = ERROR_MESSAGE
    
    # 상태 업데이트
    state["answer"] = answer
    state["model_used"] = settings.GENERATOR_MODEL
    
    return state