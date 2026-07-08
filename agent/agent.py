from agent.agent_models import AgentResponse, BrainRequest, MessageDTO, ToolCall
from agent.prompt import SYSTEM_PROMPT

class Agent:
    def __init__(self, brain, tool_registry):
        self._brain = brain
        self._tool_registry = tool_registry

    async def respond(self, history: list[MessageDTO], current_message: MessageDTO) -> AgentResponse:
        formatted_history = self._format_history(history)

        request = BrainRequest(
            system_prompt=SYSTEM_PROMPT,
            history=formatted_history,
            tools=self._tool_registry.get_tools(),
        )

        response = await self._brain.generate(request)

        if (response.moderation_result and response.moderation_result.message_action == "delete"):
            response.tool_calls.append(
                ToolCall(
                    name="delete_message",
                    arguments={
                        "message_id": current_message.message_id,
                        "channel_id": current_message.channel_id
                    }
                )
            )
        
        return response

    def _format_history(self, history: list[MessageDTO]) -> list[dict]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in history
        ]