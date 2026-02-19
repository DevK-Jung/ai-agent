"""Agent workflow constants"""

class WorkflowSteps:
    """워크플로우 단계 상수"""
    CLASSIFIER = "classifier"
    ROUTER = "router"
    GENERATOR = "generator"
    SEARCH_GENERATOR = "search_generator"
    SUMMARY_GENERATOR = "summary_generator"
    COMPARE_GENERATOR = "compare_generator"
    
class StreamEventTypes:
    """스트림 이벤트 타입 상수"""
    START = "start"
    PROGRESS = "progress"
    CHUNK = "chunk"
    COMPLETE = "complete"
    ERROR = "error"

class StreamMessages:
    """스트림 메시지 상수"""
    ANALYZING_QUESTION = "질문을 분석하고 있습니다..."
    CLASSIFYING_QUESTION = "질문 유형을 분석 중입니다..."
    GENERATING_ANSWER = "답변을 생성하고 있습니다..."
    PROCESSING_ERROR = "죄송합니다. 처리 중 오류가 발생했습니다."
    
    @staticmethod
    def question_type_classified(question_type: str) -> str:
        return f"질문 유형: {question_type}"