import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button
from utils import shared, helpers
from services.global_economy import GlobalEconomyService
from cogs.economy import ECONOMY_GROUP, ECONOMY_ADMIN_GROUP
from cogs.economy.paginator import ShopPaginator

class GlobalEconomy(shared.GroupedCog):
    """
    Commands for the overarching Global Economy and Guild Prestige.
    """
    group = app_commands.Group(name="global", description="Global economy commands", parent=ECONOMY_GROUP)

    def __init__(self) -> None:
        super().__init__()
        self.service = GlobalEconomyService()
    
    @app_commands.command(name="profile", description="View your global profile, including Yume Coins and other global statistics.")
    async def view_profile(self, interaction: discord.Interaction, target: discord.Member = None) -> None:
        user_to_check = target or interaction.user
        db_user = self.service._get_user(user_to_check.id)
        
        if not db_user:
            await interaction.response.send_message("Profile not found. Play a game to initialize!", ephemeral=True)
            return
            
        active = db_user.active_items # TODO: add active_items to the User class in models
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

    @app_commands.command(name="shop", description="Browse items available in the global shop.")
    async def global_shop(self, interaction: discord.Interaction) -> None:
        items = self.service.get_global_shop_items()
        if not items:
            embed = helpers.embed_generator(title="Global Shop", description="The shop is currently empty.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        view = ShopPaginator(
            shop_items=items,
            user_id=interaction.user.id,
            buy_command="",
            shop_name=guild.name,
            currency=currency
        )
        await interaction.response.send_message(embed=view.generate_embed(), view=view)
        view.original_message = await interaction.original_response()

    @app_commands.command(name="buy", description="Purchase an item from the global shop using Yume Coins.")
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

    @app_commands.command(name="leaderboard", description="View the top servers ranked by Yume Points.")
    async def guild_leaderboard(self, interaction: discord.Interaction) -> None:
        guilds = self.service.get_top_guilds(
            guild_id=interaction.guild.id,
            number_of_guilds=10
        )
        
        embed = helpers.embed_generator(
            title="Global Guild Leaderboard",
            description="",
        )
        for i, guild in enumerate(guilds, 1):
            points = getattr(guild, 'yume_points', 0)
            embed.add_field(name=f"#{i} {guild.name}", value=f"`{points} YP`", inline=False)
            
        await interaction.response.send_message(embed=embed)

class GlobalEconomyAdmin(shared.GroupedCog):
    """
    _summary_
    """
    group = ECONOMY_ADMIN_GROUP

    def __init__(self):
        super().__init__()
        self.service = GlobalEconomyService()

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="tax", description="Set this server's Yume Coin tax rate (0-30%). (Admin)")
    async def set_tax(self, interaction: discord.Interaction, percentage: int = None) -> None:
        """_summary_

        Args:
            interaction (discord.Interaction): _description_
            percentage (int, optional): _description_. Defaults to None.
        """
        guild_id = interaction.guild.id
        
        if percentage is None:
            guild_tax_rate = self.service.get_guild_tax(guild_id)
            embed = helpers.embed_generator(
                title="Tax Rate",
                description=f"Server's tax rate is `{guild_tax_rate}`"
            )

        if not (0 <= percentage <= 30):
            embed = helpers.embed_generator(
                title="Tax Rate",
                description=f"Server's tax rate must be between 0 and 30."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        decimal_rate = percentage / 100.0
        success = self.service.set_guild_tax(interaction.guild.id, decimal_rate)
        
        if success:
            embed = helpers.embed_generator(
                title="Tax Rate Updated",
                description=f"Guild tax is now set to **{percentage}%**.",
                color=discord.Color.green()
            )
        else:
            embed = helpers.embed_generator(
                title="Tax Rate Error",
                description="Failed to update guild's tax rate.",
                color=discord.Color.red()
            )
            
        await interaction.response.send_message(embed=embed)

async def setup() -> None:
    if shared.GLOBAL_CONFIG["features"]["economy"]["global"]["is_enabled"]:
        await shared.SHIRAYUME.add_cog(GlobalEconomy(), override=True)
        await shared.SHIRAYUME.add_cog(GlobalEconomyAdmin(), override=True)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            function_name="cogs.global_economy.setup",
            description="Setup completed successfully"
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            function_name="cogs.global_economy.setup",
            description="Global economy is disabled, setup skipped"
        )