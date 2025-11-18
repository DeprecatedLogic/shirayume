#from typing import List
from datetime import datetime, timezone, timedelta
from services import polls_service
import discord
from discord.ui import View, Button, Select
from discord import app_commands
from discord.ext import commands
from utils import shared, helpers

class PollCreationView(View):
    def __init__(self, timeout = 300):
        super().__init__(timeout = timeout)
        self.question = ""
        self.options = []
        self.duration_days = 0
        self.duration_hours = 0
        self.duration_minutes = 0
        self.duration_seconds = 0

    @discord.ui.select(
        placeholder = "Select number of options (2-50)",
        options = [discord.SelectOption(label = str(i), value = str(i)) for i in range(2, 51)]
    ) # can omit value since it will default to the label but I used it for the experience :P
    async def option_count(self, interaction: discord.Interaction, select: Select):
        num_options = int(select.values[0])
        self.options = [""] * num_options
        await interaction.response.send_modal(PollOptionsModal(self))
    
    @discord.ui.button(label = "Set Duration", style = discord.ButtonStyle.primary)
    async def set_duration(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PollDurationModal(self))
    
    @discord.ui.button(label = "Create Poll", style = discord.ButtonStyle.green)
    async def create_poll(self, interaction: discord.Interaction, button: Button):
        if (
            not self.question or not all(self.options) or
            self.duration_days + self.duration_hours + self.duration_minutes + self.duration_seconds == 0
        ):
            await interaction.response.send_message(content = "Please complete all fields.", ephemeral = True)
            return
        
        poll = {
            "poll_id": -1,
            "guild_id": interaction.guild_id,
            "creator_id": interaction.user.id,
            "question": self.question,
            "options": self.options,
            "votes": {option: 0 for option in self.options},
            "is_active": True,
            "created_at": datetime.now(),
            "is_dirty": True
        }
        if await polls_service.create_poll(poll):
            embed = helpers.embed_generator(
                title = poll["question"],
                description = "\n".join(f"{i+1}. {option}" for i, option in enumerate(poll["options"])),
                color = (128, 0, 128)
            )
            embed.add_field(name = "Status", value = "Open", inline = False)
            embed.set_footer(text = f"Poll ID: {poll['poll_id']} | Created by {interaction.user.name}")
            await interaction.response.send_message(embed = embed)
            self.stop()
        else:
            await interaction.response.send_message(
                content = "Failed to create poll.",
                ephemeral = True
            )

class PollOptionsModal(discord.ui.Modal):
    def __init__(self, view: PollCreationView):
        super().__init__(title = "Enter Poll Options")
        self.view = view
        for i in range(len(view.options)):
            self.add_item(discord.ui.TextInput(
                label = f"Option {i+1}",
                placeholder = f"Enter option {i+1}",
                max_length = 100
            ))
    
    async def on_submit(self, interaction: discord.Interaction):
        self.view.options = [child.value for child in self.children]
        await interaction.response.send_message(content = "Option set! Set duration next.", ephemeral = True)

class PollDurationModal(discord.ui.Modal):
    days = discord.ui.TextInput(label = "Days (0-90)", default = "0", max_length = 2)
    hours = discord.ui.TextInput(label = "Hours (0-23)", default = "0", max_length = 2)
    minutes = discord.ui.TextInput(label = "Minutes (0-59)", default = "0", max_length = 2)
    seconds = discord.ui.TextInput(label = "Seconds (0-59)", default = "0", max_length = 2)

    def __init__(self, view: PollCreationView):
        super().__init__(title = "Set Poll Duration")
        self.view = view
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            days = int(self.days.value)
            hours = int(self.hours.value)
            minutes = int(self.minutes.value)
            seconds = int(self.seconds.value)

            if (
                days < 0 or
                days > 90 or
                hours < 0 or
                hours > 23 or
                minutes < 0 or
                minutes > 59 or
                seconds < 0 or
                seconds > 59
            ):
                await interaction.response.send_message(
                    content = "Invalid duration. Use 0-90 days, 0-23 hours, 0-59 seconds",
                    ephemeral = True
                )
                return
            self.view.duration_days = days
            self.view.duration_hours = hours
            self.view.duration_minutes = minutes
            self.view.duration_seconds = seconds
            await interaction.response.send_message(
                content = "Duration set! Click 'Create Poll' to finish.",
                ephemeral = True
            )
        except ValueError:
            await interaction.response.send_message(
                content = "Enter valid numbers for duration.",
                ephemeral = True
            )

class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name = "yumepoll", description = "Create a new poll")
    async def create_poll(self, interaction: discord.Interaction, question: str):
        if len(question) > 255:
            await interaction.response.send_message(
                content = "Question must be 255 characters or less.",
                ephemeral = True
            )
            return
        view = PollCreationView()
        view.question = question
        embed = helpers.embed_generator(
            title = "Create Your Poll",
            description = "Select options and duration.",
            color = (128, 0, 128)
        )
        await interaction.response.send_message(embed = embed, view = view, ephemeral = True)

    async def close_poll():
        pass

    async def show_polls():
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Poll(bot))