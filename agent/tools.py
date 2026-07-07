from agent.agent_models import ToolDefinition
from agent.context import DiscordToolContext

async def delete_message(context: DiscordToolContext, channel_id: int, message_id: int):
    channel = context.bot.get_channel(channel_id)

    message = await channel.fetch_message(message_id)
    print(f"Deleting {message_id}")
    await message.delete()

    return {
        "success": True,
        "message_id": message_id,
    }

delete_message_tool = ToolDefinition(
    name="delete_message",
    description=(
        "Deletes a Discord message. "
        "Use this when a message violates moderation rules "
        "and should be removed."
    ),
    parameters={
        "message_id": {
            "type": "integer",
            "description": "The ID of the message to delete."
        }
    },
    function=delete_message,
)