from enum import Enum


class PromptRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"