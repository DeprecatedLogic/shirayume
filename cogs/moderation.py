from datetime import datetime, timezone, timedelta
from services import moderation
import discord
from discord import app_commands
from discord.ext import commands
from utils import shared, helpers
import asyncio

class Moderation(commands.Cog):

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.kick(reason=reason)
            embed = helpers.embed_generator(
                title="Kick",
                description=f"{member.mention} has been sent to touch grass. Reason: {reason}",
                color=(205, 85, 0)
            )
            await interaction.response.send_message(embed=embed)

            moderation.add_moderation_logs(
                guild_id=interaction.guild.id,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action_type=shared.Action.kick,
                reason=reason,
                action_timestamp=datetime.now(timezone.utc),
                duration_minutes=0,
                is_active=True,
                pardoned=False
            )

        except discord.Forbidden:
            embed = helpers.embed_generator(
                title="Kick",
                description="You don't have permission to kick this member."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = helpers.embed_generator(
                title="Kick",
                description=f"Failed to kick {member.mention}. Error: {e}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_member(self, interaction: discord.Interaction, member: discord.Member, reason: str="No reason provided"):
        try:
            await member.ban(reason=reason)
            embed = helpers.embed_generator(
                title="Ban",
                description=f"{member.mention} went for milk. Reason: {reason}",
                color=(255, 0, 0)
            )
            await interaction.response.send_message(embed=embed)

            moderation.add_moderation_logs(
                guild_id=interaction.guild.id,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action_type=shared.Action.ban,
                reason=reason,
                action_timestamp=datetime.now(timezone.utc),
                duration_minutes=0,
                is_active=True,
                pardoned=False
            )

        except discord.Forbidden:
            embed = helpers.embed_generator(
                title="Ban",
                description="You don't have permission to ban this member.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = helpers.embed_generator(
                title="Ban",
                description=f"Failed to ban {member.mention}. Error: {e}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="unban", description="Unban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_member(self, interaction: discord.Interaction, user: discord.User):
        try:
            await interaction.guild.unban(user)
            embed = helpers.embed_generator(
                title="Ban",
                description=f"{user.mention} has returned with the milk.",
                color=(0, 255, 0)
            )
            await interaction.response.send_message(embed=embed)

            moderation.add_moderation_logs(
                guild_id=interaction.guild.id,
                user_id=user.id,
                moderator_id=interaction.user.id,
                action_type=shared.Action.unban,
                reason=None,
                action_timestamp=datetime.now(timezone.utc),
                duration_minutes=0,
                is_active=True,
                pardoned=False
            )

        except discord.Forbidden:
            embed = helpers.embed_generator(
                title="Ban",
                description="You don't have permission to unban this member.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = helpers.embed_generator(
                title="Ban",
                description=f"Failed to unban {user.mention}. Error: {e}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="timeout", description="Timeout a member for a custom duration")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_member(self, interaction: discord.Interaction, member: discord.Member, hours: int=0, minutes: int=0, seconds: int=0, reason: str="No reason provided"):

        duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        if duration.total_seconds() <= 0:
            embed = helpers.embed_generator(
                title="Timeout",
                description="Duration must be greater than 0.",
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        until = discord.utils.utcnow() + duration

        try:
            await member.timeout(until, reason=reason)
            embed = helpers.embed_generator(
                title="Timeout",
                description=f"{member.mention} has lost speech priveleges for {hours}h {minutes}m {seconds}s. Reason: {reason}",
                color=(255, 200, 0)
            )
            await interaction.response.send_message(embed=embed)

            moderation.add_moderation_logs(
                guild_id=interaction.guild.id,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action_type=shared.Action.mute,
                reason=reason,
                action_timestamp=datetime.now(timezone.utc),
                duration_minutes=duration.total_seconds() // 60,
                is_active=True,
                pardoned=False
            )   
            
        except discord.Forbidden:
            embed = helpers.embed_generator(
                title="Timeout",
                description="You don't have permission to timeout this member.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = helpers.embed_generator(
                title="Timeout",
                description=f"Failed to timeout {member.mention}. Error: {e}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)   


    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout_member(self, interaction: discord.Interaction, member: discord.Member, reason: str="No reason provided"):
        if not member.timed_out_until:
            embed = helpers.embed_generator(
                title="Untimeout",
                description=f"{member.mention} is not currently timed out.",
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        try:
            await member.timeout(None, reason=reason)
            embed = helpers.embed_generator(
                title="Untimeout",
                description=f"Timeout removed for {member.mention} . Reason: {reason}",
                color=(255, 200, 0)
            )
            await interaction.response.send_message(embed=embed)

            moderation.add_moderation_logs(
                guild_id=interaction.guild.id,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action_type=shared.Action.unmute,
                reason=reason,
                action_timestamp=datetime.now(timezone.utc),
                duration_minutes=0,
                is_active=True,
                pardoned=False
            )

        except discord.Forbidden:
            embed = helpers.embed_generator(
                title="Untimeout",
                description="You don't have permission to remove this member's timeout.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = helpers.embed_generator(
                title="Untimeout",
                description=f"Failed to remove timeout for {member.mention}. Error: {e}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_member(self, interaction: discord.Interaction, member: discord.Member, reason: str="No reason provided"):
        try:
            embed = helpers.embed_generator(
                title="Warn",
                description=f"{member.mention} has been warned. Reason: {reason}",
                color=(255, 85, 0)
            )
            await interaction.response.send_message(embed = embed)

            moderation.add_moderation_logs(
                guild_id=interaction.guild.id,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action_type=shared.Action.warn,
                reason=reason,
                action_timestamp=datetime.now(timezone.utc),
                duration_minutes=0,
                is_active=True,
                pardoned=False
            )
            
        except discord.Forbidden:
            embed = helpers.embed_generator(
                title="Warn",
                description="You don't have permission to warn this member.",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)

        except Exception as e:
            embed = helpers.embed_generator(
                title="Warn",
                description=f"Failed to warn {member.mention}. Error: {e}",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)


    @app_commands.command(name="purge", description="Purge messages from a member in the current channel")
    @app_commands.checks.has_permissions(manage_messages=True, read_message_history=True)
    async def purge_messages_from_member(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount < 1 or amount > 100:
            embed = helpers.embed_generator(
                title="Purge",
                description="Please provide an amount between 1 and 100.",
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True, thinking=True)
        message_followup = None

        try:
            channel: discord.TextChannel = interaction.channel

            recent_messages: list[discord.Message] = []
            old_messages: list[discord.Message] = []

            # The hard limit is 14 days
            # We use 13 days and 23 hours to be absolutely safe
            cutoff_datetime = discord.utils.utcnow() - timedelta(days=13, hours=23)

            embed = helpers.embed_generator(
                title="Purge",
                description=f"Searching messages from {member.mention} in this channel...",
            )
            message_followup = await interaction.followup.send(embed=embed, ephemeral=True)

            async for message in channel.history(limit=None):
                if message.author.id == member.id:
                    
                    # Check if it's a recent message
                    if message.created_at >= cutoff_datetime:
                        recent_messages.append(message)
                    else:
                        old_messages.append(message)

                    amount -= 1

                    # Stop searching once we have found the amount requested
                    if amount <= 0:
                        break

            total_messages = len(recent_messages) + len(old_messages)
            total_messages_deleted = total_messages
            
            embed = helpers.embed_generator(
                title="Purge",
                description=f"Deleting {total_messages} messages...",
            )
            await message_followup.edit(embed=embed)

            # Bulk delete recent messages (fast)
            await channel.delete_messages(recent_messages)
            
            # Delete old messages one by one (slower, has to respect Discord's rate-limit)
            for message in old_messages:
                try:
                    await message.delete()
                    await asyncio.sleep(0.5)
                except discord.NotFound:
                    total_messages_deleted -= 1

            embed = helpers.embed_generator(
                title="Purge",
                description=f"Deleted {total_messages_deleted}/{total_messages} messages from {member.mention}.",
            )
            await message_followup.edit(embed=embed)

            moderation.add_moderation_logs(
                guild_id=interaction.guild.id,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action_type=shared.Action.purge,
                reason=f"Deleted {total_messages_deleted}/{total_messages} messages in {channel.mention} from {member.mention}.",
                action_timestamp=datetime.now(timezone.utc),
                duration_minutes=0,
                is_active=True,
                pardoned=False
            )

        except discord.Forbidden:
            embed = helpers.embed_generator(
                title="Purge",
                description="You don't have permission to purge messages in this channel.",
            )
            if message_followup:
                await message_followup.edit(embed=embed)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            embed = helpers.embed_generator(
                title="Purge",
                description=f"Failed to purge messages. Error: {e}",
            )
            if message_followup:
                await message_followup.edit(embed=embed)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)


async def setup():
    await shared.SHIRAYUME.add_cog(Moderation(), override=True)
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        function_name="cogs.moderation.setup",
        description="Setup completed successfully"
    )
