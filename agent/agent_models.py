from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class MessageDTO:
    channel_id: int
    author: str
    role: str
    content: str

@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]

@dataclass
class AgentResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

@dataclass
class BrainRequest:
    system_prompt: str
    history: list[dict]
    tools: list[ToolDefinition]

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict
    function: Callable