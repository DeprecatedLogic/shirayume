import datetime
from services import moderation_service
import discord
from discord import app_commands
from discord.ext import commands
from utils import shared

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"{member.mention} has been kicked. Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick this member.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick {member.mention}. Error: {e}", ephemeral=True)
            return
    
        moderation_service.importe(
            mlog_id = -1,
            guild_id = interaction.guild.id,
            user_id = member.id,
            moderator_id = interaction.user.id,
            action_type = shared.Action.kick,
            reason = reason,
            action_timestamp = datetime.datetime.now(),
            duration_minutes = 0,
            is_active = True,
            pardoned = False
        )


    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"{member.mention} has been banned. Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban this member.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban {member.mention}. Error: {e}", ephemeral=True)
            return
        
        moderation_service.importe(
            mlog_id = -1,
            guild_id = interaction.guild.id,
            user_id = member.id,
            moderator_id = interaction.user.id,
            action_type = shared.Action.kick,
            reason = reason,
            action_timestamp = datetime.datetime.now(),
            duration_minutes = 0,
            is_active = True,
            pardoned = False
        )


    @app_commands.command(name="unban", description="Unban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_member(self, interaction: discord.Interaction, user: discord.User):
        try:
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"{user.mention} has been unbanned.")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to unban this member.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"Failed to unban {user.mention}. Error: {e}", ephemeral=True)
            return
        
        moderation_service.importe(
            mlog_id = -1,
            guild_id = interaction.guild.id,
            user_id = user.id,
            moderator_id = interaction.user.id,
            action_type = shared.Action.unban,
            reason = None,
            action_timestamp = datetime.datetime.now(),
            duration_minutes = 0,
            is_active = True,
            pardoned = False
        )


    @app_commands.command(name="timeout", description="Timeout a member for a custom duration")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_member(self, interaction: discord.Interaction, member: discord.Member, hours: int = 0, minutes: int = 0, seconds: int = 0, reason: str = "No reason provided"):

        duration = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        if duration.total_seconds() <= 0:
            return await interaction.response.send_message("Duration must be greater than 0.", ephemeral=True)

        until = discord.utils.utcnow() + duration

        try:
            await member.timeout(until, reason=reason)
            await interaction.response.send_message(
                f"{member.mention} has been timed out for {hours}h {minutes}m {seconds}s. Reason: {reason}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to timeout this member.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout {member.mention}. Error: {e}", ephemeral=True)
            return

        moderation_service.importe(
            mlog_id = -1,
            guild_id = interaction.guild.id,
            user_id = member.id,
            moderator_id = interaction.user.id,
            action_type = shared.Action.mute,
            reason = reason,
            action_timestamp = datetime.datetime.now(),
            duration_minutes = duration.total_seconds() // 60,
            is_active = True,
            pardoned = False
        )      


    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not member.timed_out_until:
            return await interaction.response.send_message(
                f"{member.mention} is not currently timed out.", ephemeral=True)
        
        try:
            await member.timeout(None, reason=reason)
            await interaction.response.send_message(f"Timeout removed for {member.mention} . Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to remove this member's timeout.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"Failed to remove timeout for {member.mention}. Error: {e}", ephemeral=True)
            return
        
        moderation_service.importe(
            mlog_id = -1,
            guild_id = interaction.guild.id,
            user_id = member.id,
            moderator_id = interaction.user.id,
            action_type = shared.Action.unmute,
            reason = reason,
            action_timestamp = datetime.datetime.now(),
            duration_minutes = 0,
            is_active = True,
            pardoned = False
        )


    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await interaction.response.send_message(f"{member.mention} has been warned. Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to warn this member.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"Failed to warn {member.mention}. Error: {e}", ephemeral=True)
            return
        
        moderation_service.importe(
            mlog_id = -1,
            guild_id = interaction.guild.id,
            user_id = member.id,
            moderator_id = interaction.user.id,
            action_type = shared.Action.warn,
            reason = reason,
            action_timestamp = datetime.datetime.now(),
            duration_minutes = 0,
            is_active = True,
            pardoned = False
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))