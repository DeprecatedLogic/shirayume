import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
import asyncio
from utils import shared, helpers
from services import statistics
import time

class Statistics(commands.Cog):
    """
    Cog responsible for tracking server metrics and structural channels.
    
    Dynamically tracks context metrics such as total user visibility rates,
    bot distributions, presence evaluations, and transforms voice structures 
    interactively using automated update throttling guards.
    """
    
    def __init__(self):
        self.stats = statistics.StatisticsService()
        self.pending_updates = {}   # Map tracking unique active asyncio tasks [guild_id -> Task]
        self.last_enable = {}       # Throttle mapping for context tracking [guild_id -> monotonic_time]
        self.update_delay = 120     # Throttling frequency delay bounds
        self.enable_delay = 180     # Interaction control block timeline constraint

    def _extract_member_data(self, guild: discord.Guild) -> list:
        """
        Converts Discord Member objects into raw data dicts for the service layer.

        Args:
            guild (discord.Guild): Target guild instance.

        Returns:
            list: Parsed structural objects detailing status and account categories.
        """
        return [
            {"is_bot": member.bot, "is_online": member.status != discord.Status.offline}
            for member in guild.members
        ]

    async def _sync_channels(self, guild: discord.Guild) -> bool:
        """
        Handles the Discord API side of updating channels.

        Args:
            guild (discord.Guild): Active guild requiring validation matching.

        Returns:
            bool: True if context mapping operation finishes successfully, False otherwise.
        """
        member_data = self._extract_member_data(guild)
        new_stats = self.stats.calculate_stats(guild.id, guild.member_count or 0, member_data)
        
        if not new_stats:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Skipping stats sync for guild {guild.id} (data missing or configuration disabled)."
            )
            return False

        tracked_ids = self.stats.get_tracked_ids(guild.id)
        category_id = tracked_ids["category_id"]
        channel_ids = tracked_ids["channel_ids"]
        
        category = guild.get_channel(category_id) if category_id else None
        expected_names = self.stats.get_expected_names(new_stats)
        
        needs_db_update = False

        try:
            # Recreate structural layouts automatically if dropped by moderators
            if not category:
                CATEGORY_NAME = shared.GLOBAL_CONFIG["features"]["statistics"]["category_name"]
                category = await guild.create_category(
                    CATEGORY_NAME,
                    reason="Statistics self-healing / setup",
                    position=0
                )
                category_id = category.id
                needs_db_update = True
                helpers.custom_print(
                    level=shared.LogLevel.INFO,
                    description=f"Self-healed category layout for guild {guild.id}."
                )

            # Iterative synchronization of downstream voice metric structures
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

            # Commit unique infrastructure layout identification modifications if changed
            if needs_db_update:
                self.stats.update_tracked_ids(guild.id, category_id, channel_ids)

        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Failed to sync stats channels for guild {guild.id}: {e}"
            )
            return False

        return True

    async def _delayed_sync(self, guild: discord.Guild) -> None:
        """Internal worker task wrapping throttled interface update loops to prevent API limits."""
        try:
            await asyncio.sleep(self.update_delay)
            await self._sync_channels(guild)
        except asyncio.CancelledError:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Delayed tracking sync worker cancelled for guild {guild.id}."
            )
            return
        finally:
            self.pending_updates.pop(guild.id, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Fires when a user enters the server bounds to reschedule statistical channels."""
        guild = member.guild

        if not self.stats.is_stats_enabled(guild.id):
            return
        
        if guild.id not in self.pending_updates:
            self.pending_updates[guild.id] = asyncio.create_task(
                self._delayed_sync(guild)
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Fires when a user leaves the server bounds to update analytics mappings."""
        guild = member.guild

        if not self.stats.is_stats_enabled(guild.id):
            return
        
        if guild.id not in self.pending_updates:
            self.pending_updates[guild.id] = asyncio.create_task(
                self._delayed_sync(guild)
            )

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        """Fires when user updates interaction attributes or client metadata scopes."""
        guild = after.guild

        if not self.stats.is_stats_enabled(guild.id):
            return
        
        if guild.id not in self.pending_updates:
            self.pending_updates[guild.id] = asyncio.create_task(
                self._delayed_sync(guild)
            )

    @app_commands.command(name="stats", description="Enable or disable server statistics")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_stats(self, interaction: discord.Interaction, action: Literal["enable", "disable"]):
        await interaction.response.defer(ephemeral=False)
        
        if action == "enable":
            last_timestamp = self.last_enable.get(interaction.guild_id, None)
            elapsed = time.monotonic() - last_timestamp if last_timestamp else self.enable_delay

            # Enforce configuration system command cooldown
            if elapsed < self.enable_delay:
                embed = helpers.embed_generator(
                    title="Statistics",
                    description=f"Please wait {int(self.enable_delay - elapsed)} seconds before enabling server statistics again.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return

            success = self.stats.enable_stats(interaction.guild_id)
            if success and await self._sync_channels(interaction.guild):
                self.last_enable[interaction.guild_id] = time.monotonic()

                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Server statistics have been **enabled** and initialized.",
                    color=discord.Color.green()
                )
                helpers.custom_print(
                    level=shared.LogLevel.INFO,
                    description=f"Statistics engine enabled and mapped for guild {interaction.guild_id}."
                )
            else:
                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Statistics are already enabled or globally disabled by Shirayume's developers.",
                )

        else: 
            to_delete = self.stats.disable_stats(interaction.guild_id)
            if to_delete:
                # Remove active dynamic components immediately
                for chan_id in to_delete.get("channel_ids", []):
                    channel = interaction.guild.get_channel(chan_id)
                    if channel:
                        await channel.delete(reason="Statistics disabled")
                
                category_id = to_delete.get("category_id")
                if category_id:
                    category = interaction.guild.get_channel(category_id)
                    if category:
                        await category.delete(reason="Statistics disabled")

                # Drop worker structures related to tracking queues
                task = self.pending_updates.pop(interaction.guild_id, None)
                if task:
                    task.cancel()

                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Server statistics have been **disabled**.",
                    color=discord.Color.orange()
                )
                helpers.custom_print(
                    level=shared.LogLevel.INFO,
                    description=f"Statistics engine dropped and removed for guild {interaction.guild_id}."
                )
            else:
                embed = helpers.embed_generator(
                    title="Statistics",
                    description="Statistics are already disabled.",
                )

        await interaction.followup.send(embed=embed)

async def setup():
    """
    Attaches and runs background operational pipelines for the Statistics metrics layer.
    """
    if shared.GLOBAL_CONFIG["features"]["statistics"].get("is_enabled", False):
        stats_cog = Statistics()
        
        # Process startup channel sweeps across active guild footprints
        for guild in shared.SHIRAYUME.guilds:
            shared.SHIRAYUME.loop.create_task(stats_cog._sync_channels(guild))
        
        await shared.SHIRAYUME.add_cog(stats_cog, override=True)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description="Statistics cog setup completed successfully."
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Statistics feature is disabled, setup skipped."
        )