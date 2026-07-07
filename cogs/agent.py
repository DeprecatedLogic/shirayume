import discord
from discord.ext import commands
from agent.agent import Agent
from agent.brain import PlaceholderBrain
from agent.tool_registry import ToolRegistry
from agent.tools import delete_message_tool
from agent.agent_models import MessageDTO
from agent.context import DiscordToolContext
from agent.conversation_manager import ConversationManager
from utils import shared


class AgentCog(commands.Cog):
    """
    """ 
    def __init__(self, conversation_manager, agent):
        self._conversation_manager = conversation_manager
        self._agent = agent

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.content:
            return

        content = message.content.replace(
            f"<@{shared.SHIRAYUME.user.id}>",
            ""
        ).strip()

        dto = MessageDTO(
            channel_id=message.channel.id,
            author=message.author.name,
            role="user",
            content=content,
        )

        self._conversation_manager.add_message(dto)
        print(dto)
        if shared.SHIRAYUME.user not in message.mentions:
            return

        history = self._conversation_manager.get_history(message.channel.id)

        response = await self._agent.respond(history)
        
        print(response)
        if response.content:
            await message.channel.send(response.content)

async def setup():
    conversation_manager = ConversationManager()

    tool_context = DiscordToolContext(
        bot=shared.SHIRAYUME
    )
    registry = ToolRegistry(context=tool_context)
    registry.register(delete_message_tool)


    brain = PlaceholderBrain()
    agent = Agent(brain=brain, tool_registry=registry)

    if "AgentCog" not in shared.SHIRAYUME.cogs:
        await shared.SHIRAYUME.add_cog(
            AgentCog(conversation_manager, agent)
        )