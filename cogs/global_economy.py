import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button
from utils import shared, helpers
from services import global_economy

class GlobalShopPaginator(View):
    def __init__(self, shop_items: list[dict]) -> None:
        super().__init__(timeout=180)
        self.shop_items = shop_items
        self.current_page = 0
        self.items_per_page = 4
        self.max_pages = max(1, (len(self.shop_items) + self.items_per_page - 1) // self.items_per_page)
        self.update_buttons()

    def generate_embed(self) -> discord.Embed:
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.shop_items))
        page_items = self.shop_items[start:end]

        embed = helpers.embed_generator(
            title=f"Global Shop (Page {self.current_page + 1}/{self.max_pages})",
            description="Use `/global buy <item_id>` to instantly equip an item.",
            color=discord.Color.gold()
        )

        for item in page_items:
            type_tag = item['item_type'].name.upper()
            embed.add_field(
                name=f"ID: {item['item_id']} | {item['name']} [{type_tag}]",
                value=f"**Price:** {item['price']} YC\n{item['description']}",
                inline=False
            )
        return embed

    def update_buttons(self) -> None:
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.max_pages - 1

    @button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="gshop_prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @button(label="Next", style=discord.ButtonStyle.secondary, custom_id="gshop_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @button(label="Close", style=discord.ButtonStyle.danger, custom_id="gshop_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        embed = helpers.embed_generator(title="Global Shop", description="Closed.")
        await interaction.response.edit_message(embed=embed, view=None)

class GlobalEconomy(commands.Cog):
    """
    Commands for the overarching Global Economy and Guild Prestige.
    """

    def __init__(self) -> None:
        self.service = global_economy.GlobalEconomyService()

    @app_commands.command(name="profile", description="View your Global User Profile")
    async def view_profile(self, interaction: discord.Interaction, target: discord.Member = None) -> None:
        user_to_check = target or interaction.user
        db_user = self.service._get_user(user_to_check.id)
        
        if not db_user:
            await interaction.response.send_message("Profile not found. Play a game to initialize!", ephemeral=True)
            return
            
        active = db_user.active_items
        color_hex = active.get("color", "ffffff").replace("#", "")
        embed_color = int(color_hex, 16) if color_hex.isalnum() else 0xffffff

        embed = discord.Embed(
            title=f"{active.get('badge', '')} {user_to_check.display_name}'s Profile",
            description=f"**Title:** {active.get('title', 'Wanderer')}",
            color=discord.Color(embed_color)
        )
        embed.add_field(name="Wallet", value=f"`{db_user.balance} Yume Coins`", inline=False)
        embed.set_thumbnail(url=user_to_check.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop_global", description="Browse the Global Shop")
    async def global_shop(self, interaction: discord.Interaction) -> None:
        items = self.service.get_global_shop_items()
        if not items:
            embed = helpers.embed_generator(title="Global Shop", description="The shop is currently empty.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        view = GlobalShopPaginator(items)
        await interaction.response.send_message(embed=view.generate_embed(), view=view)

    @app_commands.command(name="buy_global", description="Purchase and equip an item from the Global Shop")
    async def buy_item(self, interaction: discord.Interaction, item_id: int) -> None:
        result = self.service.purchase_global_item(interaction.user.id, item_id)
        
        if not result["success"]:
            embed = helpers.embed_generator("Transaction Failed", result["reason"], discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        item = result["item"]
        embed = helpers.embed_generator(
            "Item Equipped!",
            f"Successfully purchased and equipped **{item.name}** for `{item.price} YC`.",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set_tax", description="[Admin] Set the Guild's Yume Coin tax rate (0 to 30)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_tax(self, interaction: discord.Interaction, percentage: int) -> None:
        if not (0 <= percentage <= 30):
            await interaction.response.send_message("Tax rate must be between 0 and 30.", ephemeral=True)
            return

        decimal_rate = percentage / 100.0
        success = self.service.set_guild_tax(interaction.guild_id, decimal_rate)
        
        if success:
            embed = helpers.embed_generator("Tax Rate Updated", f"Guild tax is now set to **{percentage}%**.", discord.Color.green())
        else:
            embed = helpers.embed_generator("Error", "Failed to update guild settings.", discord.Color.red())
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the top Guilds by Yume Points")
    async def guild_leaderboard(self, interaction: discord.Interaction) -> None:
        db = self.service._get_guild(interaction.guild_id) # Just to ensure cache access
        manager = global_economy.database_manager.DB_MANAGER
        
        guilds = sorted(manager.guilds, key=lambda g: getattr(g, 'yume_points', 0), reverse=True)[:10]
        
        embed = helpers.embed_generator(title="Global Guild Leaderboard", description="", color=discord.Color.purple())
        for idx, g in enumerate(guilds, 1):
            points = getattr(g, 'yume_points', 0)
            embed.add_field(name=f"#{idx} {g.name}", value=f"`{points} YP`", inline=False)
            
        await interaction.response.send_message(embed=embed)

async def setup() -> None:
    if shared.GLOBAL_CONFIG["features"]["economy"]["global"]["is_enabled"]:
        await shared.SHIRAYUME.add_cog(GlobalEconomy(), override=True)
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            function_name="cogs.global_economy.setup",
            description="Global economy is disabled, setup skipped"
        )