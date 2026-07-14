import discord
from utils import shared, helpers

class ShopPaginator(discord.ui.View):
    """
    A pagination view for navigating the Guild or Global Shop.
    """

    def __init__(
        self,
        shop_items: list[dict], user_id: int, buy_command: str,
        shop_name: str = "Local", currency: str = "Credits", items_per_page: int = 4
    ) -> None:
        """
        Initializes a shop paginator view.  

        Args:
            shop_items (list[dict]): A list of dictionaries containing shop item data.
            user_id (int): The ID of the user browsing the shop.
            buy_command (str): The command to use when buying an item from this shop.
            shop_name (str, optional): The name of the shop. Default is "Local". (The word "Shop" is always appended)
            currency (str, optional): The name of the currency. Default is "Credits".
            items_per_page (int, optional): The number of items to show per page. Default is 4.
        """
        super().__init__(timeout=180)
        self.shop_items = shop_items
        self.user_id = user_id
        self.buy_command = buy_command
        self.shop_name = shop_name
        self.currency = currency
        self.items_per_page = items_per_page
        self.current_page = 0
        self.max_pages = max(1, (len(self.shop_items) + self.items_per_page - 1) // self.items_per_page)
        self.original_message: Union[discord.Message | None] = None
        self.update_buttons()

    async def on_timeout(self) -> None:
        try:
            self.stop()
            embed = helpers.embed_generator(title=f"{self.shop_name} Shop", description="The shop has been closed automatically.")
            await self.original_message.edit(embed=embed, view=None)
        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                function_name="cogs.economy.paginator.ShopPaginator.close_button",
                description=f"Failed to close server's shop with exception: {e}"
            )
            embed = helpers.embed_generator(
                title="Closing Error",
                description="Failed to close server's shop.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, view=None, ephemeral=True)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Checks if the user interacting is the original user.

        Args:
            interaction (discord.Interaction): The interaction object.

        Returns:
            bool: True if the user is the original user, otherwise False.
        """
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You can't interact with someone else's shop.",
                ephemeral=True,
            )
            return False

        return True

    def generate_embed(self) -> discord.Embed:
        """
        Generates the embed for the current page of the shop.

        Returns:
            discord.Embed: The formatted embed displaying up to 4 shop items.
        """
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.shop_items))
        page_items = self.shop_items[start:end]

        embed = helpers.embed_generator(
            title=f"{self.shop_name} Shop (Page {self.current_page + 1}/{self.max_pages})",
            description=f"Use `{self.buy_command} <item_id>` to buy an item.",
            color=discord.Color.gold()
        )

        for item in page_items:
            item_type = item.get('item_type')
            type_tag = f" [{item_type.name.upper()}]" if item_type else ""

            embed.add_field(
                name=f"**Name:** {item.get('name', 'Unnamed')}{type_tag} ({item.get('item_id', 'Unidentified')})",
                value=f"**Price:** `{item.get('price', 'Unknown')} {self.currency}`\n{item.get('description', 'No description.')}",
                inline=False
            )

        return embed

    def update_buttons(self) -> None:
        """
        Updates the state of the navigation buttons based on the current page.
        """
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.max_pages - 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
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

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
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

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Closes the shop view and removes the buttons.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button that was pressed.
        """
        try:
            self.stop()
            embed = helpers.embed_generator(title=f"{self.shop_name} Shop", description="The shop has been closed.")
            await self.original_message.edit(embed=embed, view=None)
        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                function_name="cogs.economy.paginator.ShopPaginator.close_button",
                description=f"Failed to close server's shop with exception: {e}"
            )
            embed = helpers.embed_generator(
                title="Closing Error",
                description="Failed to close server's shop.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, view=None, ephemeral=True)

