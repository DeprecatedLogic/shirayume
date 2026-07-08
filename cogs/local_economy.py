import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button
from utils import shared, helpers
from services.local_economy import EconomyService

class ShopPaginator(View):
    """
    A pagination view for navigating the Guild Shop.
    """

    def __init__(self, shop_items: list[dict], guild_name: str, currency: str, user_id: int) -> None:
        """
        Initializes the ShopPaginator view.

        Args:
            shop_items (list[dict]): A list of dictionaries containing shop item data.
            guild_name (str): The name of the guild where the shop is located.
            currency (str): The name of the guild's local currency.
            user_id (int): The ID of the user browsing the shop.
        """
        super().__init__(timeout=180)
        self.shop_items = shop_items
        self.guild_name = guild_name
        self.currency = currency
        self.user_id = user_id
        self.current_page = 0
        self.items_per_page = 5
        self.max_pages = max(1, (len(self.shop_items) + self.items_per_page - 1) // self.items_per_page)
        self.update_buttons()

    def generate_embed(self) -> discord.Embed:
        """
        Generates the embed for the current page of the shop.

        Returns:
            discord.Embed: The formatted embed displaying up to 5 shop items.
        """
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.shop_items))
        page_items = self.shop_items[start:end]

        embed = helpers.embed_generator(
            title=f"{self.guild_name} Shop (Page {self.current_page + 1}/{self.max_pages})",
            description="Use `/buy <item_name>` to purchase an item."
        )

        for item in page_items:
            embed.add_field(
                name=f"{item.get('name')} — {item.get('price')} {self.currency}",
                value=item.get('description', 'No description provided.'),
                inline=False
            )
        return embed

    def update_buttons(self) -> None:
        """
        Updates the state of the navigation buttons based on the current page.
        """
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.max_pages - 1

    @button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="shop_prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Navigates to the previous page in the shop.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button that was pressed.
        """
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @button(label="Next", style=discord.ButtonStyle.secondary, custom_id="shop_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Navigates to the next page in the shop.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button that was pressed.
        """
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @button(label="Close", style=discord.ButtonStyle.danger, custom_id="shop_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Closes the shop view and removes the buttons.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button that was pressed.
        """
        self.stop()
        embed = helpers.embed_generator(
            title=f"{self.guild_name} Shop",
            description="Closed the shop as requested."
        )
        await interaction.response.edit_message(embed=embed, view=None)


class LocalEconomy(commands.Cog):
    """
    Handles Discord UI and events for the local server economy.
    """

    def __init__(self) -> None:
        """
        Initializes the LocalEconomy Cog.
        """
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

    @app_commands.command(name="balances", description="Displays your wallet balance for each mutual server.")
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
            description="Here are your current funds across mutual servers:"
        )
        for guild in guilds:
            currency: str = self.service.get_guild_currency(guild.id)
            balance: int = self.service.get_balance(guild.id, user.id)
            embed.add_field(
                name=f"**Server:** {guild.name}",
                value=f"**> Balance:** {balance} {currency}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=private)

    @commands.guild_only()
    @app_commands.command(name="balance", description="Check your local server balance")
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
    @app_commands.command(name="transfer", description="Send money to another member")
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
    @app_commands.command(name="shop_local", description="View the local server shop")
    async def view_shop(self, interaction: discord.Interaction) -> None:
        """
        Displays available items for purchase using a paginated view.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        user: discord.Member = interaction.user
        guild: discord.Guild = interaction.guild
        
        shop_items: list = self.service.get_shop_items(guild.id)
        if not shop_items:
            embed = helpers.embed_generator(
                title="Empty Shop",
                description=f"No items found in the {guild.name} shop."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        currency: str = self.service.get_guild_currency(guild.id)
        
        view = ShopPaginator(shop_items=shop_items, guild_name=guild.name, currency=currency, user_id=user.id)
        embed = view.generate_embed()
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.guild_only()
    @app_commands.command(name="buy_local", description="Purchase an item from the local shop")
    async def buy_item(self, interaction: discord.Interaction, item_name: str) -> None:
        """
        Initiates a purchase. Atomically checks balance, deducts funds, 
        and assigns roles if applicable.
        
        Args:
            interaction (discord.Interaction): The interaction object.
            item_name (str): The exact name of the item to purchase.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        guild: discord.Guild = interaction.guild
        user: discord.Member = interaction.user
        
        result: dict = self.service.purchase_item(guild.id, user.id, item_name)
        
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

    @app_commands.command(name="add_money", description="[Admin] Add money to a user's balance")
    @app_commands.checks.has_permissions(administrator=True)
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

async def setup() -> None:
    if shared.GLOBAL_CONFIG["features"]["economy"]["local"]["is_enabled"]:
        await shared.SHIRAYUME.add_cog(LocalEconomy(), override=True)
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            function_name="cogs.economy.setup",
            description="Local economy is disabled, setup skipped"
        )