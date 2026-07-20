import json
import discord
from services.global_economy import GlobalEconomyService
from discord.ext import commands
from utils import shared, helpers

class JSONConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> dict:
        try:
            # Cleans up surrounding quotes if the user provides them
            clean_arg = argument.strip('"').replace('\\"', '"')
            return json.loads(clean_arg)
        except json.JSONDecodeError:
            raise commands.BadArgument("Invalid JSON format. Ensure quotes are escaped or wrapped correctly.")

class AdminEconomy(commands.Cog):

    def __init__(self):
        self.service = GlobalEconomyService()

    @commands.is_owner()
    @commands.command(name="add_gitem")
    async def add_global_item(self, ctx: commands.Context, name: str, price: int, item_type: str, metadata: JSONConverter, description: str) -> None:
        """ 
        Adds a new item to the Global Shop. 
        
        Note:
            Wrap the JSON metadata in single quotes to protect the double quotes.
        
        **Example Usage:**  
            !>add_gitem "Golden Name" 500 title '{"value": "King"}' "A cool title for kings"
        """
        result = self.service.add_global_shop_item(
            name=name,
            price=price,
            item_type_name=item_type,
            metadata=metadata,
            description=description
        )

        if result.get("success"):
            embed = helpers.embed_generator(
                title="Global Item Added",
                description=f"Successfully injected **{name}** into the global economy.",
                color=(79, 213, 128)
            )
            embed.add_field(name="Price", value=f"`{price} YC`", inline=True)
            embed.add_field(name="Type", value=f"`{item_type}`", inline=True)
            embed.add_field(name="Metadata", value=f"```json\n{json.dumps(metadata, indent=2)}\n```", inline=False)
            
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Global item '{name}' added successfully."
            )
        else:
            embed = helpers.embed_generator(
                title="Operation Failed",
                description=result.get("reason", "An unknown error occurred."),
                color=(204, 166, 0)
            )

        await ctx.send(embed=embed)

    @add_global_item.error
    async def add_global_item_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Catches pre-invoke parsing errors and check failures, sending them directly to Discord."""
        embed = helpers.embed_generator(
            title="Command Execution Failed",
            description=f"**Error:** {error}\n\nCheck your formatting! Make sure you are using straight quotes (`\"` and `'`) and that your price is a valid integer.",
            color=discord.Color.red
        )
        await ctx.send(embed=embed)

async def setup() -> None:
    await shared.SHIRAYUME.add_cog(AdminEconomy(), override=True)
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description="Admin economy cog setup completed successfully."
    )
