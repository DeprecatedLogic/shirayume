from agent.agent_models import AgentResponse, BrainRequest

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
    async def generate(self, request: BrainRequest) -> AgentResponse:
        ...