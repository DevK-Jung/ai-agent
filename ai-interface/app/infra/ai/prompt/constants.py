from enum import Enum


class PromptRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class PromptType(str, Enum):
    ANALYSIS = "analysis"
    CODE_GENERATION = "code_generation"