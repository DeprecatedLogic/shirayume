import discord
from discord.ext import commands
from agent.agent import Agent
from agent.brain import LlamaCppBrain
from agent.tool_registry import ToolRegistry
from agent.tools import delete_message_tool
from agent.agent_models import MessageDTO
from agent.context import DiscordToolContext
from agent.conversation_manager import ConversationManager
from utils import shared, helpers


class AgentCog(commands.Cog):
    """
    Cog driving core LLM execution interactions and automated tool calls.
    
    Hooks message contexts dynamically into structural histories and dispatches 
    asynchronous pipeline updates to local LLM engines.
    """
    
    def __init__(self, conversation_manager: ConversationManager, agent: Agent, tool_registry: ToolRegistry):
        self._conversation_manager = conversation_manager
        self._agent = agent
        self._tool_registry = tool_registry

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Processes messaging entries within mapped channels to update interaction states."""
        if message.author.bot:
            return

        if not message.content:
            return

        # Map structural objects into pipeline DTO wrappers
        dto = MessageDTO(
            message_id=message.id,
            channel_id=message.channel.id,
            author=message.author.display_name,
            role="user",
            content=message.content,
        )

        self._conversation_manager.add_message(dto)
        history = self._conversation_manager.get_history(message.channel.id)

        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Forwarding conversation history for channel {message.channel.id} to agent pipeline."
        )

        # Contact model orchestration layer
        response = await self._agent.respond(history, dto)
        print(response.moderation_result)
        print(response.tool_calls)
        
        # Fire downstream tool integrations returned from model processing
        for tool_call in response.tool_calls:
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Executing tool call: {tool_call.function.name if hasattr(tool_call, 'function') else tool_call} triggered by agent workflow."
            )
            await self._tool_registry.execute(tool_call)

async def setup() -> None:
    """
    Assembles dependent infrastructure layers and initializes the LLM Agent wrapper.
    """
    if shared.GLOBAL_CONFIG["features"]["agent"].get("is_enabled", False):
        conversation_manager = ConversationManager()

        tool_context = DiscordToolContext(
            bot=shared.SHIRAYUME
        )
        registry = ToolRegistry(context=tool_context)
        registry.register(delete_message_tool)

        # Core engine initialization sequence points
        brain = LlamaCppBrain(url="http://localhost:8080")
        agent = Agent(brain=brain, tool_registry=registry)

        await shared.SHIRAYUME.add_cog(
            AgentCog(conversation_manager, agent, registry),
            override=True
        )
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description="Agent cog setup completed successfully."
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Agent feature is disabled, setup skipped."
        )