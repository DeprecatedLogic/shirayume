import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button
from utils import shared, helpers
from services.local_economy import EconomyService
from cogs.economy import ECONOMY_GROUP, ECONOMY_ADMIN_GROUP
from cogs.economy.paginator import ShopPaginator

class LocalEconomy(shared.GroupedCog):
    """
    Handles Discord UI and events for the local server economy.
    """
    group = app_commands.Group(name="local", description="Server economy commands", parent=ECONOMY_GROUP)

    def __init__(self) -> None:
        """
        Initializes the LocalEconomy Cog.
        """
        super().__init__()
        self.service = EconomyService()
    
    @commands.guild_only()
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Passive listener to reward users for activity.
        
        Args:
            message (discord.Message): The message sent by a user.
        """
        if message.author.bot or not message.guild:
            return
        
        amount_rewarded: int = self.service.process_message_reward(message.guild.id, message.author.id)

    @app_commands.command(name="wallets", description="View your wallet balances across all mutual servers.")
    async def check_all_balances(self, interaction: discord.Interaction, private: bool = True) -> None:
        """
        Displays the user's wallet balance across all mutual guilds.

        Args:
            interaction (discord.Interaction): The interaction object.
            private (bool, optional): Whether the response should be ephemeral. Defaults to True.
        """
        user = interaction.user
        guilds = getattr(user, 'mutual_guilds', [])
        
        if not guilds:
            await interaction.response.send_message("No mutual servers found.", ephemeral=private)
            return

        embed = helpers.embed_generator(
            title="Balance per Server",
            description="Here are your current funds across mutual servers."
        )
        for guild in guilds:
            currency: str = self.service.get_guild_currency(guild.id)
            balance: int = self.service.get_balance(guild.id, user.id)
            embed.add_field(
                name=f"**{guild.name}**",
                value=f"> {balance} {currency}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=private)

    @commands.guild_only()
    @app_commands.command(name="wallet", description="View your wallet balance in this server.")
    async def check_balance(self, interaction: discord.Interaction, member: discord.Member = None, private: bool = True) -> None:
        """
        Displays a user's wallet balance in the current guild.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member, optional): The target member to check. Admins only. Defaults to None.
            private (bool, optional): Whether the response should be ephemeral. Defaults to True.
        """
        target_user: discord.Member = member if (
            member is not None and interaction.user.guild_permissions.administrator
        ) else interaction.user
        
        currency: str = self.service.get_guild_currency(interaction.guild.id)
        balance: int = self.service.get_balance(interaction.guild.id, target_user.id)

        embed = helpers.embed_generator(
            title="Balance",
            description=f"{target_user.name}'s balance is: `{balance} {currency}`"
        )
        await interaction.response.send_message(embed=embed, ephemeral=private)

    @commands.guild_only()
    @app_commands.command(name="transfer", description="Send money to another member in this server.")
    async def pay_member(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        """
        Transfers funds between users within the same guild.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member): The recipient of the funds.
            amount (int): The amount of currency to send.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        sender: discord.Member = interaction.user

        if member.bot or sender.id == member.id:
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description=f"Operation failed: Cannot transfer funds to {'a bot' if member.bot else 'yourself'}.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
            
        if amount <= 0:
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description="Operation failed: Amount must be greater than 0.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        guild: discord.Guild = interaction.guild

        if self.service.transfer_funds(guild.id, sender.id, member.id, amount):
            currency: str = self.service.get_guild_currency(guild.id)
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description=f"Successfully transferred `{amount} {currency}` to user {member.mention}.",
                color=discord.Color.green()
            )
            
            # Attempt to DM the receiver
            receiver_embed = helpers.embed_generator(
                title="Balance Update",
                description=f"Received `{amount} {currency}` from {sender.name} ({guild.name})."
            )
            try:
                receiver_channel = member.dm_channel or await member.create_dm()
                await receiver_channel.send(embed=receiver_embed)
            except discord.Forbidden:
                pass # Silently ignore if user has DMs disabled
            
        else:
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description="Operation failed: Insufficient funds.",
                color=discord.Color.red()
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.guild_only()
    @app_commands.command(name="shop", description="Browse items available in this server's shop.")
    async def view_shop(self, interaction: discord.Interaction) -> None:
        """
        Displays available items for purchase using a paginated view.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer(thinking=True)

        user: discord.Member = interaction.user
        guild: discord.Guild = interaction.guild

        try:
            shop_items: list = self.service.get_shop_items(guild.id)
            if not shop_items:
                embed = helpers.embed_generator(
                    title="Empty Shop",
                    description=f"No items found in the {guild.name} shop."
                )
                await interaction.followup.send(embed=embed)
                return

            currency: str = self.service.get_guild_currency(guild.id)
            
            view = ShopPaginator(
                shop_items=shop_items,
                user_id=user.id,
                buy_command=f"/economy local buy",
                shop_name=guild.name,
                currency=currency
            )
            await interaction.followup.send(embed=view.generate_embed(), view=view)
            view.original_message = await interaction.original_response()
            
        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                function_name="cogs.economy.local.LocalEconomy.view_shop",
                description=f"Failed to open server's shop with exception: {e}"
            )
            embed = helpers.embed_generator(
                title="Shop Error",
                description="Failed to open server's shop.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @commands.guild_only()
    @app_commands.command(name="buy", description="Purchase an item from this server's shop.")
    async def buy_item(self, interaction: discord.Interaction, item_id: int) -> None:
        """
        Initiates a purchase. Atomically checks balance, deducts funds, 
        and assigns roles if applicable.
        
        Args:
            interaction (discord.Interaction): The interaction object.
            item_id (str): The exact ID of the item to purchase.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        guild: discord.Guild = interaction.guild
        user: discord.Member = interaction.user
        
        result: dict = self.service.purchase_item(guild.id, user.id, item_id)
        
        if not result.get("success"):
            embed = helpers.embed_generator(
                title="Purchase Failed",
                description=result.get("reason", "An error occurred during the transaction."),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        item_data: dict = result.get("item", {})
        currency: str = self.service.get_guild_currency(guild.id)
        
        embed = helpers.embed_generator(
            title="Purchase Successful!",
            description=f"You successfully bought **{item_data.get('name')}** for `{item_data.get('price')} {currency}`.",
            color=discord.Color.green()
        )

        role_id = item_data.get("role_id")
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await user.add_roles(role, reason=f"Purchased {item_data.get('name')} in shop.")
                    embed.add_field(
                        name="Role Granted",
                        value=f"You have been given the {role.mention} role!",
                        inline=False
                    )
                except discord.Forbidden:
                    embed.add_field(
                        name="Warning", 
                        value="I don't have permission to give you this role. Please contact an admin.", 
                        inline=False
                    )
                except discord.HTTPException as e:
                    embed.add_field(name="Error", value=f"Failed to grant role: {e}", inline=False)
            else:
                embed.add_field(
                    name="Warning",
                    value="The role associated with this item no longer exists on the server.",
                    inline=False
                )

        await interaction.followup.send(embed=embed, ephemeral=True)

class LocalEconomyAdmin(shared.GroupedCog):
    """
    _summary_
    """
    group = ECONOMY_ADMIN_GROUP

    def __init__(self) -> None:
        """
        Initializes the LocalEconomyAdmin Cog.
        """
        super().__init__()
        self.service = EconomyService()

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mint", description="Give local currency to a member. (Admin)")
    async def admin_add_money(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        """
        Allows admins to mint new currency and give it to a specific user.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member): The user receiving the funds.
            amount (int): The amount of currency to mint and add.
        """
        guild = interaction.guild

        original_balance = self.service.get_balance(guild.id, member.id)
        new_balance = self.service.add_balance(guild.id, member.id, amount)

        if new_balance > original_balance:
            currency = self.service.get_guild_currency(guild.id)
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description=f"Successfully added `{amount} {currency}` to {member.name}'s balance.",
                color=discord.Color.green()
            )
            
            receiver_embed = helpers.embed_generator(
                title="Balance Update",
                description=f"Received `{amount} {currency}` from an Admin ({guild.name})."
            )

            try:
                if not member.bot:
                    receiver_channel = member.dm_channel or await member.create_dm()
                    await receiver_channel.send(embed=receiver_embed)
            except discord.Forbidden:
                pass # Silently ignore if user has DMs disabled
                
        else:
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description="Operation failed: Invalid amount.",
                color=discord.Color.red()
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="additem", description="Add a new item to this server's shop. (Admin)")
    async def admin_add_item(self, interaction: discord.Interaction, name: str, price: int, description: str, role: discord.Role = None) -> None:
        """
        Adds a new item to the local server shop.

        Args:
            interaction (discord.Interaction): The interaction object.
            name (str): The name of the item.
            price (int): The cost of the item.
            description (str): A brief description of the item.
            role (discord.Role, optional): The role to assign upon purchase.
        """
        if price <= 0:
            await interaction.response.send_message("Operation failed: Price must be greater than 0.", ephemeral=True)
            return

        role_id = role.id if role else None

        try:
            success = self.service.add_shop_item(
                guild_id=interaction.guild.id,
                name=name,
                price=price,
                description=description,
                role_id=role_id
            )
            if success:
                currency = self.service.get_guild_currency(interaction.guild.id)
                embed = helpers.embed_generator(
                    title="Shop Updated",
                    description=f"Successfully added **{name}** to the shop for `{price} {currency}`.",
                    color=discord.Color.green()
                )
                if role:
                    embed.add_field(name="Attached Role", value=role.mention, inline=False)
            else:
                raise Exception("`add_shop_item` failed")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = helpers.embed_generator(
                title="Shop Error",
                description="Failed to add the item to the server's shop.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                function_name="cogs.economy.local.LocalEconomyAdmin.admin_add_item",
                description=f"Failed to add a local item with exception: {e}"
            )

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="delitem", description="Remove an existing item from this server's shop. (Admin)")
    async def admin_remove_item(self, interaction: discord.Interaction, item_id: int) -> None:
        """
        Removes an item from the local server shop by its ID.

        Args:
            interaction (discord.Interaction): The interaction object.
            item_id (int): The unique ID of the item to delete.
        """
        success = self.service.remove_shop_item(
            guild_id=interaction.guild.id, 
            item_id=item_id
        )

        if success:
            embed = helpers.embed_generator(
                title="Shop Updated",
                description=f"Successfully removed item ID `{item_id}` from the shop.",
                color=discord.Color.green()
            )
        else:
            embed = helpers.embed_generator(
                title="Shop Error",
                description=f"Operation failed: Item ID `{item_id}` not found or already removed.",
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup() -> None:
    if shared.GLOBAL_CONFIG["features"]["economy"]["local"]["is_enabled"]:
        await shared.SHIRAYUME.add_cog(LocalEconomy(), override=True)
        await shared.SHIRAYUME.add_cog(LocalEconomyAdmin(), override=True)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            function_name="cogs.local_economy.setup",
            description="Setup completed successfully"
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            function_name="cogs.economy.setup",
            description="Local economy is disabled, setup skipped"
        )