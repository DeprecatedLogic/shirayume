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
        """
        Fetches and displays a user's global profile, showing balance and custom items.

        Args:
            interaction (discord.Interaction): The interaction object.
            target (discord.Member, optional): The member to view. Defaults to None.
        """
        user_to_check = target or interaction.user
        db_user = self.service._get_user(user_to_check.id)
        
        # If user isn't in DB, they haven't used the bot yet
        if not db_user:
            helpers.custom_print(level=shared.LogLevel.DEBUG, description=f"Profile lookup failed for {user_to_check.id}")
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

    @app_commands.command(name="shop", description="Browse items available in the global shop.")
    async def global_shop(self, interaction: discord.Interaction) -> None:
        """
        Displays the global shop items in a paginated view.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        items = self.service.get_global_shop_items()
        if not items:
            helpers.custom_print(level=shared.LogLevel.INFO, description="Global shop empty.")
            embed = helpers.embed_generator(title="Global Shop", description="The shop is currently empty.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        view = ShopPaginator(
            shop_items=items,
            user_id=interaction.user.id,
            buy_command="/global buy",
            shop_name="Global",
            currency="Yume Coins"
        )
        await interaction.response.send_message(embed=view.generate_embed(), view=view)
        view.original_message = await interaction.original_response()

    @app_commands.command(name="buy", description="Purchase an item from the global shop using Yume Coins.")
    async def buy_item(self, interaction: discord.Interaction, item_id: int) -> None:
        """
        Handles the purchase logic for global shop items.

        Args:
            interaction (discord.Interaction): The interaction object.
            item_id (int): The ID of the item to purchase.
        """
        result = self.service.purchase_global_item(interaction.user.id, item_id)
        
        # Log failures for debugging specific user transaction issues
        if not result["success"]:
            helpers.custom_print(level=shared.LogLevel.WARNING, description=f"Global purchase failed for {interaction.user.id}: {result['reason']}")
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
        """
        Displays the top 10 guilds ranked by Yume Points.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
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
    Administrative commands for managing the Global Economy.
    """
    group = ECONOMY_ADMIN_GROUP

    def __init__(self):
        super().__init__()
        self.service = GlobalEconomyService()

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="tax", description="Set this server's Yume Coin tax rate (0-30%). (Admin)")
    async def set_tax(self, interaction: discord.Interaction, percentage: int = None) -> None:
        """
        Updates or views the server's global tax rate.

        Args:
            interaction (discord.Interaction): The interaction object.
            percentage (int, optional): The tax percentage to set. Defaults to None.
        """
        guild_id = interaction.guild.id
        
        if percentage is None:
            guild_tax_rate = self.service.get_guild_tax(guild_id)
            embed = helpers.embed_generator(
                title="Tax Rate",
                description=f"Server's tax rate is `{guild_tax_rate * 100}%`"
            )
            await interaction.response.send_message(embed=embed)
            return

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
            helpers.custom_print(level=shared.LogLevel.INFO, description=f"Tax updated to {percentage}% for guild {guild_id}.")
            embed = helpers.embed_generator(
                title="Tax Rate Updated",
                description=f"Guild tax is now set to **{percentage}%**.",
                color=discord.Color.green()
            )
        else:
            helpers.custom_print(level=shared.LogLevel.ERROR, description=f"Failed tax update for guild {guild_id}.")
            embed = helpers.embed_generator(
                title="Tax Rate Error",
                description="Failed to update guild's tax rate.",
                color=discord.Color.red()
            )
            
        await interaction.response.send_message(embed=embed)

async def setup() -> None:
    # Only register these if the config actually has them enabled
    if shared.GLOBAL_CONFIG["features"]["economy"]["global"]["is_enabled"]:
        await shared.SHIRAYUME.add_cog(GlobalEconomy(), override=True)
        await shared.SHIRAYUME.add_cog(GlobalEconomyAdmin(), override=True)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description="Global economy cog setup completed successfully."
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Global economy feature is disabled, setup skipped."
        )