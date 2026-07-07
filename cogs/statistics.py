import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
import asyncio
from utils import shared, helpers
from services import statistics

class Statistics(commands.Cog):
    def __init__(self):
        self.stats = statistics.StatisticsService()

    def _extract_member_data(self, guild: discord.Guild) -> list:
        """Converts Discord Member objects into raw data dicts for the service layer."""
        return [
            {"is_bot": member.bot, "is_online": member.status != discord.Status.offline}
            for member in guild.members
        ]

    async def _sync_channels(self, guild: discord.Guild) -> bool:
        """Handles the Discord API side of updating channels."""
        member_data = self._extract_member_data(guild)
        new_stats = self.stats.calculate_stats(guild.id, guild.member_count or 0, member_data)
        
        if not new_stats:
            return False

        tracked_ids = self.stats.get_tracked_ids(guild.id)
        category_id = tracked_ids["category_id"]
        channel_ids = tracked_ids["channel_ids"]
        
        category = guild.get_channel(category_id) if category_id else None
        expected_names = self.stats.get_expected_names(new_stats)
        
        needs_db_update = False

        try:
            # Ensure Category
            if not category:
                CATEGORY_NAME = shared.GLOBAL_CONFIG["features"]["statistics"]["category_name"]
                category = await guild.create_category(
                    CATEGORY_NAME,
                    reason="Statistics self-healing / setup",
                    position=0
                )
                category_id = category.id
                needs_db_update = True

            # Ensure Channels
            for key, expected_name in expected_names.items():
                channel = guild.get_channel(channel_ids.get(key))
                
                if not channel:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(connect=False, speak=False)
                    }
                    channel = await guild.create_voice_channel(
                        name=expected_name,
                        category=category,
                        overwrites=overwrites,
                        reason="Statistics self-healing / setup"
                    )
                    channel_ids[key] = channel.id
                    needs_db_update = True
                    await asyncio.sleep(0.5)
                elif channel.name != expected_name:
                    await channel.edit(name=expected_name)
                    await asyncio.sleep(0.5)

            # Update DB if any IDs changed
            if needs_db_update:
                self.stats.update_tracked_ids(guild.id, category_id, channel_ids)

        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                function_name="cogs.statistics._sync_channels",
                description=f"Failed to sync stats channels for guild {guild.id}: {e}"
            )
            return False

        return True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._sync_channels(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self._sync_channels(member.guild)

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if after.bot:
            return
        await self._sync_channels(after.guild)

    @app_commands.command(name="yumestats", description="Enable or disable server statistics")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_stats(self, interaction: discord.Interaction, action: Literal["enable", "disable"]):
        await interaction.response.defer(ephemeral=False)
        
        if action == "enable":
            success = self.stats.enable_stats(interaction.guild_id)
            if success and await self._sync_channels(interaction.guild):
                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Server statistics have been **enabled** and initialized.",
                    color=discord.Color.green()
                )
            else:
                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Statistics are already enabled or globally disabled by Shirayume's developers.",
                    color=discord.Color.orange()
                )

        else: # action == "disable"
            to_delete = self.stats.disable_stats(interaction.guild_id)
            if to_delete:
                # Delete tracked channels
                for chan_id in to_delete.get("channel_ids", []):
                    channel = interaction.guild.get_channel(chan_id)
                    if channel:
                        await channel.delete(reason="Statistics disabled")
                
                # Delete tracked category
                category_id = to_delete.get("category_id")
                if category_id:
                    category = interaction.guild.get_channel(category_id)
                    if category:
                        await category.delete(reason="Statistics disabled")

                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Server statistics have been **disabled**.",
                    color=discord.Color.orange()
                )
            else:
                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Statistics are already disabled.",
                    color=discord.Color.red()
                )

        await interaction.followup.send(embed=embed)

async def setup():
    stats_cog = Statistics()
    
    for guild in shared.SHIRAYUME.guilds:
        shared.SHIRAYUME.loop.create_task(stats_cog._sync_channels(guild))

    if "Statistics" not in shared.SHIRAYUME.cogs:
        await shared.SHIRAYUME.add_cog(stats_cog)