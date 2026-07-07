from agent.agent_models import AgentResponse, BrainRequest, ModerationResult
import httpx
import json

class Brain:
    async def generate(self, history):
        raise NotImplementedError
    
class PlaceholderBrain(Brain):
    async def generate(self, request: BrainRequest) -> AgentResponse:
        return AgentResponse(
            content="I received your message.",
            tool_calls=[]
        )
    
class LlamaCppBrain(Brain):
    def __init__(self, url: str):
        self._url = url

    async def generate(self, request: BrainRequest) -> AgentResponse:

        messages = [
            {
                "role": "system",
                "content": request.system_prompt,
            },
            *request.history,
        ]

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._url}/v1/chat/completions",
                json={
                    "messages": messages,
                },
            )

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        result = json.loads(content)

        moderation = ModerationResult(
            category=result["category"],
            severity=result["severity"],
            explanation=result["explanation"],
            message_action=result["message_action"],
            user_action=result["user_action"],
            needs_human_review=result["needs_human_review"]
        )

        return AgentResponse(
            moderation_result=moderation,
            tool_calls=[]
        )