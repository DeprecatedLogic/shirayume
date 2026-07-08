import discord
from discord.ext import commands
from agent.agent import Agent
from agent.brain import LlamaCppBrain
from agent.tool_registry import ToolRegistry
from agent.tools import delete_message_tool
from agent.agent_models import MessageDTO
from agent.context import DiscordToolContext
from agent.conversation_manager import ConversationManager
from utils import shared


class AgentCog(commands.Cog):
    """
    """ 
    def __init__(self, conversation_manager, agent, tool_registry):
        self._conversation_manager = conversation_manager
        self._agent = agent
        self._tool_registry = tool_registry

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.content:
            return

        dto = MessageDTO(
            message_id=message.id,
            channel_id=message.channel.id,
            author=message.author.display_name,
            role="user",
            content=message.content,
        )

        self._conversation_manager.add_message(dto)

        history = self._conversation_manager.get_history(message.channel.id)

        response = await self._agent.respond(history, dto)
        print(response.moderation_result)
        print(response.tool_calls)
        for tool_call in response.tool_calls:
            await self._tool_registry.execute(tool_call)

async def setup():
    conversation_manager = ConversationManager()

    tool_context = DiscordToolContext(
        bot=shared.SHIRAYUME
    )
    registry = ToolRegistry(context=tool_context)
    registry.register(delete_message_tool)


    brain = LlamaCppBrain(url="http://localhost:8080")
    agent = Agent(brain=brain, tool_registry=registry)

    await shared.SHIRAYUME.add_cog(
        AgentCog(conversation_manager, agent),
        override=True
    )
