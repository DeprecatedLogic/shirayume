import discord
from typing import List
from services.matchmaking.shared import GameType
from services.matchmaking.manager import MATCHMAKING_MANAGER
from cogs.matchmaking import embeds, helpers
from utils import shared

class MoveModal(discord.ui.Modal, title="Submit Your Chess Move"):
    move_input = discord.ui.TextInput(
        label="Move Notation",
        placeholder="e.g. e2e4 or Nf3",
        min_length=2,
        max_length=7,
        required=True
    )

    def __init__(self, match_id: str):
        super().__init__()
        self.match_id = match_id

    async def on_submit(self, interaction: discord.Interaction):
        move = self.move_input.value.strip()
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        match = MATCHMAKING_MANAGER.get_user_match(user_id)
        
        success, result = MATCHMAKING_MANAGER.process_move(guild_id, user_id, {"move": move})

        if not success:
            await interaction.response.send_message(f"❌ {result.get('reason', 'Invalid move.')}", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Move `{move}` applied!", ephemeral=True)
        
        if match:
            await helpers.update_match_threads(
                bot=interaction.client, 
                match=match, 
                last_move_user=user_id, 
                last_move_uci=result.get("move")
            )

class LobbyView(discord.ui.View):
    def __init__(self, leader: discord.User, game_type: GameType):
        super().__init__(timeout=300)
        self.leader = leader
        self.game_type = game_type
        self.team_members: List[discord.User] = [leader]
        self._is_processing = False

    @discord.ui.button(label="Join Team", style=discord.ButtonStyle.success)
    async def join_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.team_members:
            await interaction.response.send_message("You are already in this lobby team.", ephemeral=True)
            return

        self.team_members.append(interaction.user)
        embed = embeds.lobby_embed(self.game_type, self.leader, self.team_members)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Leave Team", style=discord.ButtonStyle.secondary)
    async def leave_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.leader:
            await interaction.response.send_message("The lobby leader cannot leave. Use Cancel instead.", ephemeral=True)
            return

        if interaction.user in self.team_members:
            self.team_members.remove(interaction.user)
            embed = embeds.lobby_embed(self.game_type, self.leader, self.team_members)
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔍 Find Match", style=discord.ButtonStyle.primary)
    async def find_match(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.leader:
            await interaction.response.send_message("Only the lobby leader can start matchmaking.", ephemeral=True)
            return

        if self._is_processing:
            await interaction.response.send_message("Matchmaking is already being processed...", ephemeral=True)
            return
        self._is_processing = True

        await interaction.response.defer()

        user_ids = [u.id for u in self.team_members]
        success, msg, match = MATCHMAKING_MANAGER.join_queue(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            user_ids=user_ids,
            game_type=self.game_type
        )

        if not success:
            self._is_processing = False
            await interaction.followup.send(f"❌ {msg}", ephemeral=True)
            return

        self.stop()
        for child in self.children:
            child.disabled = True
            
        await interaction.edit_original_response(content=f"✅ {msg}", embed=None, view=self)

        if match:
            await helpers.setup_match_threads(interaction.client, match)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.leader:
            await interaction.response.send_message("Only the lobby leader can cancel the lobby.", ephemeral=True)
            return
        
        self.stop()
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(content="❌ Lobby cancelled.", embed=None, view=self)


class MatchView(discord.ui.View):
    def __init__(self, match_id: str):
        super().__init__(timeout=None)
        self.match_id = match_id

    @discord.ui.button(label="♟️ Make Move", style=discord.ButtonStyle.primary, custom_id="gvg_make_move")
    async def make_move(self, interaction: discord.Interaction, button: discord.ui.Button):
        match = MATCHMAKING_MANAGER.get_user_match(interaction.user.id)
        if not match or match.match_id != self.match_id:
            await interaction.response.send_message("You are not active in this match.", ephemeral=True)
            return

        if match.game.current_turn_guild_id != interaction.guild_id:
            await interaction.response.send_message("It is not your guild's turn!", ephemeral=True)
            return

        await interaction.response.send_modal(MoveModal(self.match_id))

    @discord.ui.button(label="🏳️ Forfeit", style=discord.ButtonStyle.danger, custom_id="gvg_forfeit")
    async def forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        match = MATCHMAKING_MANAGER.get_user_match(interaction.user.id)
        
        success, result = MATCHMAKING_MANAGER.forfeit_match(interaction.guild_id, interaction.user.id)
        if success:
            await interaction.response.send_message("🏳️ Your guild has forfeited the match.", ephemeral=False)
            if match:
                await helpers.update_match_threads(interaction.client, match, interaction.user.id)
        else:
            await interaction.response.send_message(f"❌ {result.get('reason')}", ephemeral=True)