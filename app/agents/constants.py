"""Agent workflow constants"""


class AgentTypes:
    """서브 에이전트 타입 상수"""
    CHAT = "chat"
    MEETING = "meeting"


class WorkflowSteps:
    """워크플로우 단계 상수"""
    # Router Workflow 노드
    SUMMARIZE_CONVERSATIONS = "summarize_conversations"
    DETECT_AGENT = "detect_agent"

    # Sub-Agent 노드
    CHAT_AGENT = "chat_agent"
    MEETING_AGENT = "meeting_agent"
    CLASSIFIER = "classifier"
    ROUTER = "router"
    GENERATOR = "generator"


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
    SUMMARIZING_CONVERSATION = "이전 대화를 요약하고 있습니다..."

    @staticmethod
    def question_type_classified(question_type: str) -> str:
        return f"질문 유형: {question_type}"
