import discord
from discord.ext import commands
from agent.agent import Agent
from agent.conversation_manager import ConversationManager
from utils import shared
from utils.agent_models import MessageDTO

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
        
        dto = MessageDTO(
            channel_id=message.channel.id,
            author=message.author.display_name,
            role="user",
            content=message.content,
        )
        self._conversation_manager.add_message(dto)

        history = self._conversation_manager.get_history(message.channel.id)

        response = await self._agent.respond(history)

        print(response)

async def setup():
    conversation_manager = ConversationManager()
    agent = Agent()

    if "AgentCog" not in shared.SHIRAYUME.cogs:
        await shared.SHIRAYUME.add_cog(
            AgentCog(conversation_manager, agent)
        )