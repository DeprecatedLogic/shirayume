import discord
from discord import app_commands
from discord.ext import commands
from utils import shared, helpers
from utils.shared import SHIRAYUME
from services import economy

class LocalEconomy(commands.Cog):
    """
    Handles Discord UI and events for the local server economy.
    """

    def __init__(self) -> None:
        self.eco_service = economy.EconomyService()
    
    @commands.guild_only()
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message, guild: discord.Guild) -> None:
        """
        Passive listener to reward users for activity.
        
        Args:
            message (discord.Message): _description_
            guild (discord.Guild): _description_
        """
        if message.author.bot:
            return
        
        amount_rewarded: int = self.eco_service.process_message_reward(guild.id, message.author.id)
        # We can log amount_rewarded or simply not do anything with it to prevent any kind of "spam"

    @app_commands.command(name="balance", description="Check your local server balance")
    async def check_balance(self, interaction: discord.Interaction, member: discord.Member = None, private: bool = True) -> None:
        """
        Displays the user's wallet balance.

        Args:
            interaction (discord.Interaction): _description_
            member (discord.Member, optional): _description_. Defaults to None.
            private (bool, optional): _description_. Defaults to True.
        """
        target_user = member if (
            member is not None and interaction.user.guild_permissions.administrator
        ) else interaction.user
        
        currency: str = self.eco_service.get_guild_currency(target_user.guild.id)
        balance: int = self.eco_service.get_balance(target_user.guild.id, target_user.id)

        embed = helpers.embed_generator(
            title="Check Balance",
            description=f"{target_user.name} balance is: `{balance} {currency}`"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="transfer", description="Send money to another member")
    async def pay_member(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        """
        Transfers funds between users.
        
        # LOGIC:
        # 1. Defer response.
        # 2. Basic validation: cannot pay bots, cannot pay self, amount must be > 0.
        # 3. Call self.eco_service.transfer_funds().
        # 4. If False: Send error embed ("Insufficient funds").
        # 5. If True: Send success embed mentioning both users and the amount transferred.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        sender = interaction.user

        if member.bot or sender.id == member.id:
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description=f"Operation failed: Cannot transfer funds to {'a bot' if member.bot else 'self'}",
                color=discord.Color.red
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        elif amount <= 0:
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description=f"Operation failed: Amount must be greater than 0",
                color=discord.Color.red
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        guild = interaction.guild

        if self.eco_service.transfer_funds(
            guild_id=guild.id,
            sender_id=sender.id,
            receiver_id=member.id,
            amount=amount
        ):
            currency = self.eco_service.get_guild_currency(guild.id)
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description=f"Successfully transfered `{amount} {currency}` to user {member.name}",
                color=discord.Color.green
            )
            
            receiver_embed = helpers.embed_generator(
                title="Trasnfer Funds",
                description=f"Received `{amount} {currency}` from {sender.name} ({guild.name})"
            )

            receiver_channel = member.dm_channel
            if receiver_channel is None:
                await member.create_dm()

            await receiver_channel.send(embed=receiver_embed)
            
        else:
            embed = helpers.embed_generator(
                title="Transfer Funds",
                description=f"Operation failed: Insufficient funds",
                color=discord.Color.red
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="shop", description="View the local server shop")
    async def view_shop(self, interaction: discord.Interaction):
        """
        Displays available items for purchase.
        
        # LOGIC:
        # 1. Call self.eco_service.get_shop_items(interaction.guild_id).
        # 2. If list is empty, send embed stating the shop is closed/empty.
        # 3. Format the items into an embed (or multiple pages using views if there are many items).
        # 4. Display Item Name, Description, and Price.
        """
        pass

    @app_commands.command(name="buy", description="Purchase an item from the shop")
    async def buy_item(self, interaction: discord.Interaction, item_name: str) -> None:
        """
        Initiates a purchase.
        
        # LOGIC:
        # 1. Defer response.
        # 2. Call a service method (e.g., purchase_item) that atomically checks balance, 
        #    deducts funds, and returns the item details.
        # 3. If deduction fails, send "Insufficient funds" embed.
        # 4. If successful, check if the item grants a Discord Role. If it does, use 
        #    interaction.user.add_roles() to assign it physically in Discord.
        # 5. Send success embed.
        """
        pass

    # --- ADMIN COMMANDS ---

    @app_commands.command(name="addmoney", description="[Admin] Add money to a user's balance")
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_add_money(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        """
        Allows admins to mint new currency.
        
        # LOGIC:
        # 1. Call self.eco_service.add_balance().
        # 2. Send an embed confirming the new funds were added.
        """
        pass

async def setup() -> None:
    await shared.SHIRAYUME.add_cog(LocalEconomy())