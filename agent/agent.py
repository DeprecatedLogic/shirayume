from utils.agent_models import AgentResponse


class PlaceholderBrain:
    async def generate(self, history: list[dict]) -> AgentResponse:
        return AgentResponse(
            content="Hello! I am alive."
        )

class Agent:
    def __init__(self):
        self._brain = PlaceholderBrain()

    async def respond(self, history: list[dict]) -> AgentResponse:
        return await self._brain.generate(history)