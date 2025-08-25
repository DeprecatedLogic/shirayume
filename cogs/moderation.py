import datetime
import discord
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_user(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} has been kicked. Reason: {reason}")


    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_user(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} has been banned. Reason: {reason}")


    @app_commands.command(name="timeout", description="Timeout a user for a custom duration")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_user(self, interaction: discord.Interaction, member: discord.Member, hours: int = 0, minutes: int = 0, seconds: int = 0, reason: str = "No reason provided"):

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
      

    @app_commands.command(name="untimeout", description="Remove timeout from a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout_user(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):

        if not member.timed_out_until:
            return await interaction.response.send_message(
                f"{member.mention} is not currently timed out.", ephemeral=True)
    
        await member.timeout(None, reason=reason)
        await interaction.response.send_message(f"Timeout removed for {member.mention} . Reason: {reason}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))