#from typing import List
import datetime as dt
from datetime import datetime
from services import polls_service
import discord
from discord.ui import View, Button, Select, TextInput
from discord import app_commands
from discord.ext import commands
from utils import shared, helpers
from typing import Union
import asyncio

class PollCreationView(View):
    def __init__(self, question: str, embed: Union[discord.Embed, None], timeout: int = 180) -> None:
        super().__init__(timeout = timeout)
        self.question = question
        self.embed = embed
        self.options = []
        self.duration_days = 0
        self.duration_hours = 0
        self.duration_minutes = 0
        self.duration_seconds = 0
        self.interaction: Union[discord.Interaction | None] = None
        self.poll_model: Union[object, None] = None

    @discord.ui.select(
        placeholder = "Select number of options (2-25)",
        options = [discord.SelectOption(label = str(i), value = str(i)) for i in range(2, 26)]
    ) # can omit value since it will default to the label but I used it for the experience :P
    async def option_count(self, interaction: discord.Interaction, select: Select) -> None:
        num_options = int(select.values[0])
        self.options = [""] * num_options
        await interaction.response.send_modal(PollOptionsModal(self))
    
    @discord.ui.button(label = "Set Duration", style = discord.ButtonStyle.primary)
    async def set_duration(self, interaction: discord.Interaction, button: Button) -> None:
        await interaction.response.send_modal(PollDurationModal(self))
    
    @discord.ui.button(label = "Create Poll", style = discord.ButtonStyle.green)
    async def create_poll(self, interaction: discord.Interaction, button: Button) -> None:
        if not self.question:
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "commands.polls.PollCreationView.create_poll",
                description = "Question is empty when creating poll."
            )
            await interaction.response.send_message(content = "An error occurred: Question is empty.", ephemeral = True)
            return None
        
        if not all(opt.strip() for opt in self.options):
            await interaction.response.send_message(content = "Please set all options.", ephemeral = True)
            return None
            
        if (self.duration_days + self.duration_hours + self.duration_minutes + self.duration_seconds) == 0:
            await interaction.response.send_message(content = "Please set a duration for the poll.", ephemeral = True)
            return None
        
        poll = {
            "poll_id": -1,
            "guild_id": interaction.guild_id,
            "creator_id": interaction.user.id,
            "question": self.question,
            "votes": {str(option): [] for option in self.options},
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "ends_at": datetime.now() + dt.timedelta(
                days = self.duration_days,
                hours = self.duration_hours,
                minutes = self.duration_minutes,
                seconds = self.duration_seconds
            ),
            "is_dirty": True
        }
        self.poll_model = await polls_service.create_poll(**poll)
        poll_model = self.poll_model

        if poll_model:
            # Rebuild the embed to show final status cleanly
            new_embed = helpers.embed_generator(
                title = self.question,
                description = "",
                color = (128, 0, 128)
            )
            status = f"Closes at {poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')} (in {str(poll_model.ends_at - datetime.now()).split('.')[0]})"
            new_embed.add_field(name = "Status", value = status, inline = False)

            options_text = "\n".join(f"`{opt}` (votes: 0)" for opt in self.options)
            new_embed.add_field(name = "Options", value = options_text, inline = False)

            new_embed.add_field(name = "Poll ID", value = poll_model.poll_id, inline = False)
            new_embed.set_footer(text = f"Created by {interaction.user.name}")
            new_embed.color = discord.Color.green()

            self.embed = new_embed
            await interaction.response.send_message(embed = new_embed)
            await self.interaction.delete_original_response() # the ephemeral setup message
            self.interaction = interaction

            async def done_callback_func():
                if Poll.poll_views.get(poll_model.poll_id) is None:
                    return
                field_index = 0
                new_embed.set_field_at(
                    field_index,
                    name = new_embed.fields[field_index].name,
                    value = f"Ended at {poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')}",
                    inline = new_embed.fields[field_index].inline
                )
                
                field_index = 1
                options_votes = zip(
                    poll_model.votes.keys(),
                    [len(voters) for voters in poll_model.votes.values()]
                )
                new_embed.set_field_at(
                    field_index,
                    name = new_embed.fields[field_index].name,
                    value = "\n".join(
                        f"`{option}` (votes: {votes})" for option, votes in options_votes
                    ),
                    inline = new_embed.fields[field_index].inline
                )
                new_embed.color = discord.Color.red()
                message = await interaction.original_response()
                await message.edit(embed = new_embed, view = None)
                Poll.poll_views.pop(poll_model.poll_id, None)
            
            task = asyncio.create_task(
                polls_service._sleep_and_finish_poll(
                    poll_id = poll_model.poll_id,
                    guild_id = poll_model.guild_id,
                    ends_at = poll_model.ends_at
                )
            )
            task.add_done_callback(lambda _: asyncio.create_task(done_callback_func()))
            Poll.poll_views[poll_model.poll_id] = self # Save the view for later reference
        else:
            await interaction.response.send_message(
                content = "Failed to create poll.",
                ephemeral = True
            )

class PollOptionsModal(discord.ui.Modal):
    def __init__(self, view: PollCreationView) -> None:
        super().__init__(title = "Enter Poll Options")
        self.view = view

        for i in range(len(view.options)):
            self.add_item(TextInput(
                label = f"Option {i+1}",
                placeholder = f"Enter option {i+1}",
                max_length = 100
            ))
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.view.options = [child.value.strip() for child in self.children]

        # Rebuild the embed
        new_embed = helpers.embed_generator(
            title = self.view.question,
            description = "Poll Options Set!",
            color = (128, 0, 128)
        )

        options_text = "\n".join(
            f"{i+1}. {opt or '*empty*'} (votes: 0)" for i, opt in enumerate(self.view.options)
        )

        new_embed.add_field(
            name = "Options:",
            value = options_text,
            inline = False
        )

        # Add the duration field if already set
        if (
            self.view.duration_days + self.view.duration_hours +
            self.view.duration_minutes + self.view.duration_seconds
        ) > 0:
            new_embed.add_field(
                name = "Duration:",
                value = (f"{self.view.duration_days:2}D {self.view.duration_hours:2}h "
                         f"{self.view.duration_minutes:2}m {self.view.duration_seconds:2}s"),
                inline = False
            )
            new_embed.add_field(
                name = "Next Step:",
                value = "Click **Create Poll**",
                inline = False
            )
        else:
            new_embed.add_field(
                name = "Next Step:",
                value = "Click **Set Duration**",
                inline = False
            )

        # Save the new embed to the view & edit the original message
        self.view.embed = new_embed
        await interaction.response.edit_message(embed = new_embed, view = self.view)

class PollDurationModal(discord.ui.Modal):
    days = TextInput(label = "Days (0-90)", default = "0", max_length = 2)
    hours = TextInput(label = "Hours (0-23)", default = "0", max_length = 2)
    minutes = TextInput(label = "Minutes (0-59)", default = "0", max_length = 2)
    seconds = TextInput(label = "Seconds (0-59)", default = "0", max_length = 2)

    def __init__(self, view: PollCreationView) -> None:
        super().__init__(title = "Set Poll Duration")
        self.view = view
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            days = int(self.days.value)
            hours = int(self.hours.value)
            minutes = int(self.minutes.value)
            seconds = int(self.seconds.value)

            if (
                days < 0 or days > 90 or
                hours < 0 or hours > 23 or
                minutes < 0 or minutes > 59 or
                seconds < 0 or seconds > 59
            ):
                await interaction.response.send_message(
                    content = "Invalid duration. Use 0-90 days, 0-23 hours, 0-59 minutes, 0-59 seconds",
                    ephemeral = True
                )
                return None
            
            self.view.duration_days = days
            self.view.duration_hours = hours
            self.view.duration_minutes = minutes
            self.view.duration_seconds = seconds
            
            new_embed = helpers.embed_generator(
                title = self.view.question,
                description = "Poll Duration Set!",
                color = (128, 0, 128)
            )
            
            # Add the options field back
            if self.view.options:
                options_text = "\n".join(
                    f"{i+1}. {opt or '*empty*'} (votes: 0)" for i, opt in enumerate(self.view.options)
                )
                new_embed.add_field(
                    name = "Options:",
                    value = options_text,
                    inline = False
                )
            else:
                new_embed.add_field(
                    name = "Options:",
                    value = "No options set yet.",
                    inline = False
                )

            # Add the new fields (duration + next step)
            new_embed.add_field(
                name = "Duration:",
                value = f"{days:2}D {hours:2}h {minutes:2}m {seconds:2}s",
                inline = False
            )
            new_embed.add_field(
                name = "Next Step:",
                value = "Click **Create Poll**" if self.view.options else "Click **Set Options**",
                inline = False
            )

            self.view.embed = new_embed
            await interaction.response.edit_message(embed = new_embed, view = self.view)
        except ValueError:
            await interaction.response.send_message(
                content = "Enter valid numbers for duration.",
                ephemeral = True
            )

class Poll(commands.Cog):
    poll_views: dict[int, PollCreationView] = {}

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name = "yumepoll", description = "Create a new poll")
    async def create_poll(self, interaction: discord.Interaction, question: str) -> None:
        if len(question) > 255:
            await interaction.response.send_message(
                content = "Question must be 255 characters or less.",
                ephemeral = True
            )
            return None
        embed = helpers.embed_generator(
            title = question,
            description = "Select options and duration.",
            color = (128, 0, 128)
        )
        view = PollCreationView(question, embed)
        view.interaction = interaction
        await interaction.response.send_message(embed = embed, view = view, ephemeral = True)

    @app_commands.command(name = "yumepollend", description = "End an existing poll")
    async def end_poll(self, interaction: discord.Interaction, poll_id: int) -> None:
        if await polls_service.end_poll(poll_id, interaction.user.id, interaction.guild_id):
            if Poll.poll_views.get(poll_id) is None:
                    return
            
            poll_view = Poll.poll_views[poll_id]
            new_embed = poll_view.embed
            poll_model = poll_view.poll_model
            poll_model.ends_at = datetime.now()

            field_index = 0
            new_embed.set_field_at(
                field_index,
                name = new_embed.fields[field_index].name,
                value = f"Ended at {poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')}",
                inline = new_embed.fields[field_index].inline
            )
            
            field_index = 1
            options_votes = zip(
                poll_model.votes.keys(),
                [len(voters) for voters in poll_model.votes.values()]
            )
            new_embed.set_field_at(
                field_index,
                name = new_embed.fields[field_index].name,
                value = "\n".join(
                    f"`{option}` (votes: {votes})" for option, votes in options_votes
                ),
                inline = new_embed.fields[field_index].inline
            )
            new_embed.color = discord.Color.red()
            message = await poll_view.interaction.original_response()
            await message.edit(embed = new_embed, view = None)
            Poll.poll_views.pop(poll_model.poll_id, None)
            
            await interaction.response.send_message(
                content = "Poll ended successfully.",
                ephemeral = True
            )
        else:
            await interaction.response.send_message(
                content = "Failed to end Poll. Something went wrong...",
                ephemeral = True
            )

    @app_commands.command(name = "yumepolls", description = "See all your active polls")
    async def show_active_polls(self, interaction: discord.Interaction, user: discord.User = None) -> None:        
        user_id = interaction.user.id if not user else user.id

        polls = await polls_service.get_active_polls(user_id, interaction.guild_id)
        if polls:
            embed = helpers.embed_generator(
                title = f"Active Polls for {self.bot.get_user(user_id)}",
                description = "",
                color = (128, 0, 128)
            )
            
            for poll in polls:
                embed.add_field(
                    name = f"\n[Poll ID {poll.poll_id}]",
                    value = poll.question,
                    inline = False
                )

                if poll.is_active:
                    time_remaining = poll.ends_at - datetime.now()
                    time_remaining_str = str(time_remaining).split(".")[0]  # Remove microseconds
                    status = f"Open (ends in {time_remaining_str})"
                else:
                    status = "Closed"

                embed.add_field(
                    name = "Status",
                    value = status,
                    inline = False
                )

                options = poll.votes.keys()
                votes = [len(v) for v in poll.votes.values()]
                results = "\n".join(
                    f"`{option}`: {votes}" for option, votes in zip(options, votes)
                )
                embed.add_field(
                    name = "Results",
                    value = results,
                    inline = False
                )

            await interaction.response.send_message(
                embed = embed,
                ephemeral = True
            )
        else:
            await interaction.response.send_message(
                content = f"User {self.bot.get_user(user_id)} doesn't have any active polls.",
                ephemeral = True,
                #delete_after = 3
            )
    
    @app_commands.command(name = "yumepollvote", description = "Vote for a poll")
    async def vote_poll(self, interaction: discord.Interaction, poll_id: int, option: str) -> None:
        if await polls_service.vote_poll(poll_id, interaction.guild_id, interaction.user.id, option):
            if Poll.poll_views.get(poll_id) is None:
                    return
            
            poll_view = Poll.poll_views[poll_id]
            new_embed = poll_view.embed
            poll_model = poll_view.poll_model

            # Update the time remaining field while we're at it
            field_index = 0
            if poll_model.is_active:
                time_remaining = poll_model.ends_at - datetime.now()
                time_remaining_str = str(time_remaining).split(".")[0]  # Remove microseconds
                status = f"Closes at {poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')} (in {time_remaining_str})"
            else:
                status = f"Ended at {poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')}"
            new_embed.set_field_at(
                field_index,
                name = new_embed.fields[field_index].name,
                value = status,
                inline = new_embed.fields[field_index].inline
            )

            # Update the votes in the embed while we're at it
            field_index = 1
            options_votes = zip(
                poll_model.votes.keys(),
                [len(voters) for voters in poll_model.votes.values()]
            )
            new_embed.set_field_at(
                field_index,
                name = new_embed.fields[field_index].name,
                value = "\n".join(
                    f"`{option}` (votes: {votes})" for option, votes in options_votes
                ),
                inline = new_embed.fields[field_index].inline
            )
            message = await poll_view.interaction.original_response()
            await message.edit(embed = new_embed, view = None)

            await interaction.response.send_message(
                content = f"You voted for option {option}.",
                ephemeral = True
            )
        else:
            await interaction.response.send_message(
                content = "Something went wrong... your vote didn't count.",
                ephemeral = True,
                delete_after = 3
            )

    @app_commands.command(name = "yumecancelvote", description = "Cancel your vote from a poll")
    async def cancel_vote(self, interaction: discord.Interaction, poll_id: int, option: str) -> None:
        if await polls_service.cancel_vote(poll_id, interaction.guild_id, interaction.user.id):
            await interaction.response.send_message(
                content = f"You cancelled your vote.",
                ephemeral = True
            )
        else:
            await interaction.response.send_message(
                content = "Something went wrong... your vote wasn't cancelled.",
                ephemeral = True,
                delete_after = 3
            )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Poll(bot))
