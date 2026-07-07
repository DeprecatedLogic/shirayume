from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class MessageDTO:
    message_id: int
    channel_id: int
    author: str
    role: str
    content: str

@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]

@dataclass
class ModerationResult:
    category: str
    severity: int
    explanation: str
    message_action: str
    user_action: str
    needs_human_review: bool

@dataclass
class AgentResponse:
    moderation_result: ModerationResult
    tool_calls: list[ToolCall] = field(default_factory=list)

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict
    function: Callable

@dataclass
class BrainRequest:
    system_prompt: str
    history: list[dict]
    tools: list[ToolDefinition]