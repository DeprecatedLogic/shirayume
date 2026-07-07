from agent.agent_models import ToolDefinition, ToolCall
from agent.context import DiscordToolContext

class ToolRegistry:
    def __init__(self, context):
        self._context = context
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    async def execute(self, tool_call: ToolCall):
        if tool_call.name not in self._tools:
            raise ValueError(
                f"Unknown tool: {tool_call.name}"
            )

        tool = self._tools[tool_call.name]

        return await tool.function(
            self._context,
            **tool_call.arguments
        )