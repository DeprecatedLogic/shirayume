import discord
from discord import app_commands
from discord.ext import commands
from utils import shared, helpers
from utils.shared import GroupedCog, RenderMode
from services.matchmaking.shared import GameType
from services.matchmaking.manager import MATCHMAKING_MANAGER
from cogs.matchmaking import embeds, views
from cogs import matchmaking

class MatchmakingCog(GroupedCog):
    group = app_commands.Group(name="matchmaking", description="Guild vs Guild Matchmaking Commands")

    def __init__(self):
        super().__init__()

    @app_commands.command(name="lobby", description="Create a GvG matchmaking lobby for your team.")
    @app_commands.choices(game=[
        app_commands.Choice(name="Chess", value="CHESS")
    ])
    async def create_lobby(self, interaction: discord.Interaction, game: app_commands.Choice[str]):
        game_type = GameType[game.value]
        
        if MATCHMAKING_MANAGER.is_guild_busy(interaction.guild_id):
            await interaction.response.send_message("❌ Your guild already has an active queue or match in progress.", ephemeral=True)
            return

        if MATCHMAKING_MANAGER.queue.is_user_queued(interaction.user.id):
            await interaction.response.send_message("❌ You are already in a matchmaking queue.", ephemeral=True)
            return

        if interaction.user.id in MATCHMAKING_MANAGER.user_active_match:
            await interaction.response.send_message("❌ You are already in an active match.", ephemeral=True)
            return

        view = views.LobbyView(leader=interaction.user, game_type=game_type)
        embed = embeds.lobby_embed(game_type, interaction.user, view.team_members)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="leave", description="Leave current matchmaking queue.")
    async def leave_queue(self, interaction: discord.Interaction):
        success, msg = MATCHMAKING_MANAGER.leave_queue(interaction.user.id)
        if success:
            await interaction.response.send_message(f"✅ {msg}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)

    @app_commands.command(name="forfeit", description="Forfeit your active GvG match.")
    async def forfeit_match(self, interaction: discord.Interaction):
        match = MATCHMAKING_MANAGER.get_user_match(interaction.user.id)
        
        success, result = MATCHMAKING_MANAGER.forfeit_match(interaction.guild_id, interaction.user.id)
        if success:
            await interaction.response.send_message("🏳️ Forfeit processed.", ephemeral=True)
            if match:
                await matchmaking.helpers.update_match_threads(interaction.client, match, interaction.user.id)
        else:
            await interaction.response.send_message(f"❌ {result.get('reason')}", ephemeral=True)

async def setup():
    """_summary_"""
    
    # TODO: Discord Bot and Database should wait for matches to end before closing
    # but it's not implemented yet (I'm tired)

    matchmaking_feature: dict = shared.GLOBAL_CONFIG["features"].get("matchmaking", {})
    if matchmaking_feature.get("is_enabled", False):

        # Setup the render mode for chess (we assume it's always enabled for now...)
        try:
            matchmaking.helpers.RENDER_MODE = RenderMode[matchmaking_feature.get("chess", {}).get("render_mode", "").upper()]
        except KeyError:
            matchmaking.helpers.RENDER_MODE = RenderMode.ASCII

        # Now we can add the Cog
        await shared.SHIRAYUME.add_cog(MatchmakingCog(), override=True)
        helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description="Matchmaking cog setup completed successfully."
            )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Matchmaking feature is disabled, setup skipped."
        )