#from typing import List
import datetime as dt
from datetime import datetime
from services import polls as polls_service
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
        self.setup_interaction: Union[discord.Interaction | None] = None
        self.poll_model: Union[object, None] = None
        self.anonymous_voting = True

    @discord.ui.button(label = "Set Options", style = discord.ButtonStyle.primary)
    async def set_options(self, interaction: discord.Interaction, button: Button) -> None:
        # Send the modal to the user
        await interaction.response.send_modal(PollOptionsModal(self))

    @discord.ui.button(label = "Set Duration", style = discord.ButtonStyle.primary)
    async def set_duration(self, interaction: discord.Interaction, button: Button) -> None:
        await interaction.response.send_modal(PollDurationModal(self))

    @discord.ui.button(label = "Anonymous Voting: ON", style = discord.ButtonStyle.green)
    async def anonymity_toggle(self, interaction: discord.Interaction, button: Button) -> None:
        self.anonymous_voting = not self.anonymous_voting
        if self.anonymous_voting:
            button.label = f"Anonymous Voting: ON"
            button.style = discord.ButtonStyle.green
            self.embed.set_footer(text = f"Anonymous Voting: Enabled")
        else:
            button.label = f"Anonymous Voting: OFF"
            button.style = discord.ButtonStyle.red
            self.embed.set_footer(text = f"Anonymous Voting: Disabled")
        await interaction.response.edit_message(embed=self.embed, view=self)
    
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
            new_embed.add_field(name = "Anonymous Voting", value = "Enabled" if self.anonymous_voting else "Disabled", inline = False)
            new_embed.add_field(name = "Poll ID", value = poll_model.poll_id, inline = True)
            new_embed.set_footer(text = f"Created by {interaction.user.name}", icon_url = interaction.user.display_avatar)
            new_embed.color = discord.Color.green()

            self.embed = new_embed
            # create the voting view (select + vote button)
            vote_view = PollVoteView(poll_model, self)

            # send the public poll message (this uses the current interaction i.e. the button interaction)
            try:
                await interaction.response.send_message(embed = new_embed, view = vote_view)
                # At this point we can stop listening for button interactions
                self.stop()
            except Exception:
                response = await polls_service.end_poll(
                    self.poll_model.poll_id,
                    self.poll_model.creator_id,
                    self.poll_model.guild_id
                )
                helpers.custom_print(
                    level=shared.LogLevel.ERROR,
                    function_name="cogs.poll_commands.PollCreationView.create_poll",
                    description="Failed to send the poll message after clicking on 'Create Poll'"
                )
                return
            
            # Store the public message object for later edits (end_poll, auto-end callback)
            public_message = await interaction.original_response()
            self.public_message = public_message

            # Delete the ephemeral setup message (self.setup_interaction was set earlier to the ephemeral setup interaction)
            try:
                await self.setup_interaction.delete_original_response()
            except Exception:
                # Ignore if already deleted or missing
                pass

            # Schedule auto-end task
            task = asyncio.create_task(
                polls_service._sleep_and_finish_poll(
                    poll_id = poll_model.poll_id,
                    guild_id = poll_model.guild_id,
                    ends_at = poll_model.ends_at
                )
            )
            # When the task completes, update the public message (use self.public_message)
            def done_callback(_future):
                async def _callback():
                    try:
                        embed = self.public_message.embeds[0]
                        embed.color = discord.Color.red()
                        field_index = 0
                        embed.set_field_at(
                            field_index,
                            name = embed.fields[field_index].name,
                            value = f"Closed at {poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')}",
                            inline = embed.fields[field_index].inline
                        )
                        field_index = 1
                        options_votes = []
                        for option, votes in poll_model.votes.items():
                            options_votes.append((option, len(votes)))
                        embed.set_field_at(
                            field_index,
                            name = embed.fields[field_index].name,
                            value = "\n".join(
                                f"`{option}` (votes: {votes}){'\nVoters: ' + ', '.join(f'<@{voter}>' for voter in poll_model.votes[option])\
                                if not self.anonymous_voting else ''}" for option, votes in options_votes
                            ),
                            inline = embed.fields[field_index].inline
                        )
                        # Add the anonymity field
                        embed.add_field(name = "Anonymous Voting", value = "Enabled" if self.anonymous_voting else "Disabled", inline = False)

                        await self.public_message.edit(embed = embed, view = None)
                    except Exception:
                        helpers.custom_print(
                            level = shared.LogLevel.ERROR,
                            function_name = "cogs.poll_commands.PollCreationView.create_poll.done_callback",
                            description = f"Failed to edit poll message after auto-end: {_future.exception()}"
                        )
                    # Remove the view from the active poll views
                    Poll.poll_views.pop(poll_model.poll_id, None)
                    return
                asyncio.create_task(_callback())
            task.add_done_callback(done_callback)

            # Keep the creation view in memory so commands can access anonymity value, etc
            Poll.poll_views[poll_model.poll_id] = self
        else:
            await interaction.response.send_message(
                content = "Failed to create poll.",
                ephemeral = True
            )

class PollOptionsModal(discord.ui.Modal):
    def __init__(self, view: PollCreationView) -> None:
        super().__init__(title = "Enter Poll Options")
        self.view = view

        # Create a single paragraph-style text input
        self.options_input = TextInput(
            label = "Options (One per line, Max 25)",
            style = discord.TextStyle.paragraph,
            placeholder = "Option 1\nOption 2\n...",
            required = True,
            max_length = 4000
        )
        self.add_item(self.options_input)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw_lines = self.options_input.value.split('\n')
        self.view.options = [line.strip() for line in raw_lines if line.strip()][:25]

        # Check if they provided at least 2 options
        if len(self.view.options) < 2:
            await interaction.response.send_message(
                content = "You must provide at least 2 options.",
                ephemeral = True
            )
            return

        # Rebuild the embed
        new_embed = helpers.embed_generator(
            title = self.view.question,
            description = "Poll Options Set!",
            color = (128, 0, 128)
        )

        options_text = "\n".join(
            f"{i+1}. {option} (votes: 0)" for i, option in enumerate(self.view.options)
        )

        new_embed.add_field(
            name = "Options",
            value = options_text,
            inline = False
        )

        # Add the duration field if already set
        if (
            self.view.duration_days + self.view.duration_hours +
            self.view.duration_minutes + self.view.duration_seconds
        ) > 0:
            new_embed.add_field(
                name = "Duration",
                value = (f"{self.view.duration_days:2} days {self.view.duration_hours:2} hours "
                         f"{self.view.duration_minutes:2} minutes {self.view.duration_seconds:2} seconds"),
                inline = False
            )
            new_embed.add_field(
                name = "Next Step:",
                value = "Click **Create Poll**",
                inline = True
            )
        else:
            new_embed.add_field(
                name = "Next Step:",
                value = "Click **Set Duration**",
                inline = True
            )

        # Add the anonymity footer
        new_embed.set_footer(text = f"Anonymous Voting: {'Enabled' if self.view.anonymous_voting else 'Disabled'}")
        # Save the new embed to the view & edit the original message
        self.view.embed = new_embed
        await interaction.response.edit_message(embed=new_embed, view=self.view)

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
                    name = "Options",
                    value = options_text,
                    inline = False
                )
            else:
                new_embed.add_field(
                    name = "Options",
                    value = "No options set yet.",
                    inline = False
                )

            # Add the new fields (duration + next step)
            new_embed.add_field(
                name = "Duration:",
                value = f"{days:2} days {hours:2} hours {minutes:2} minutes {seconds:2} seconds",
                inline = False
            )
            new_embed.add_field(
                name = "Next Step:",
                value = "Click **Create Poll**" if self.view.options else "Click **Set Options**",
                inline = False
            )

            # Add the anonymity footer
            new_embed.set_footer(text = f"Anonymous Voting: {'Enabled' if self.view.anonymous_voting else 'Disabled'}")
            # Save the new embed to the view & edit the original message
            self.view.embed = new_embed
            await interaction.response.edit_message(embed = new_embed, view = self.view)
        except ValueError:
            await interaction.response.send_message(
                content = "Enter valid numbers for duration.",
                ephemeral = True
            )

class PollOptionSelector(discord.ui.Select):
    def __init__(self, options: list[str]):
        opts = [discord.SelectOption(label=opt, value=opt) for opt in options]
        super().__init__(
            placeholder = "Pick an option to vote for...",
            min_values = 1,
            max_values = 1,
            options = opts
        )

    async def callback(self, interaction: discord.Interaction):
        # Save selection on the parent view (PollVoteView)
        parent: "PollVoteView" = self.view  # type: ignore
        parent.selected_option = self.values[0]
        # Defer so UI doesn't show the "This interaction failed" toast
        await interaction.response.defer(ephemeral = True)

class PollVoteView(discord.ui.View):
    def __init__(self, poll_model: polls_service.models.Poll, poll_view: PollCreationView):
        super().__init__(timeout = None)
        self.poll_model = poll_model
        self.poll_view = poll_view
        self.selected_option: Union[str, None] = None

        # Build and add the selector from the poll options
        options = list(self.poll_model.votes.keys())
        self.selector = PollOptionSelector(options)
        self.add_item(self.selector)

    @discord.ui.button(label = "Vote", style = discord.ButtonStyle.success, row = 4)
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Must have picked something
        if not self.selected_option:
            return await interaction.response.send_message("Pick an option first.", ephemeral = True)

        # Record the vote
        ok = await polls_service.vote_poll(
            poll_id = self.poll_model.poll_id,
            guild_id = self.poll_model.guild_id,
            user_id = interaction.user.id,
            option = self.selected_option
        )
        if not ok:
            return await interaction.response.send_message("Something went wrong, vote not recorded.", ephemeral = True)

        # Rebuild the embed to reflect updated votes
        new_embed = helpers.embed_generator(
            title = self.poll_view.question,
            description = "",
            color = (128, 0, 128)
        )

        # Status field: active or ended
        if self.poll_model.is_active:
            time_remaining = self.poll_model.ends_at - datetime.now()
            time_remaining_str = str(time_remaining).split(".")[0]
            status = f"Closes at {self.poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')} (in {time_remaining_str})"
            new_embed.color = discord.Color.green()
        else:
            status = f"Ended at {self.poll_model.ends_at.strftime('%Y-%m-%d %H:%M:%S')}"
            new_embed.color = discord.Color.red()
        new_embed.add_field(name = "Status", value = status, inline = False)

        # Options + counts (and optionally voters)
        option_lines = []
        for option, voters in self.poll_model.votes.items():
            votes_count = len(voters)
            if not self.poll_view.anonymous_voting and votes_count > 0:
                # Use mention formatting so users are clickable in message: <@user_id>
                voters_str = ", ".join(f"<@{v}>" for v in voters)
                option_lines.append(f"`{option}` (votes: {votes_count})\nVoters: {voters_str}")
            else:
                option_lines.append(f"`{option}` (votes: {votes_count})")
        new_embed.add_field(name = "Options", value = "\n".join(option_lines) if option_lines else "No options", inline = False)

        # Anonymity field
        new_embed.add_field(name = "Anonymous Voting", value = "Enabled" if self.poll_view.anonymous_voting else "Disabled", inline = False)
        new_embed.add_field(name = "Poll ID", value = self.poll_model.poll_id, inline = True)
        new_embed.set_footer(text = f"Created by {shared.SHIRAYUME.get_user(self.poll_model.creator_id).name}", icon_url = shared.SHIRAYUME.get_user(self.poll_model.creator_id).display_avatar)

        self.poll_view.embed = new_embed
        # Edit the message in-place. The message containing the select+vote button is available as interaction.message
        try:
            await interaction.message.edit(embed = new_embed, view = self)
        except Exception:
            # Fallback: if for some reason interaction.message isn't editable, try stored public_message
            if getattr(self.poll_view, "public_message", None):
                try:
                    await self.poll_view.public_message.edit(embed = new_embed, view = self)
                except Exception as e:
                    helpers.custom_print(
                        level = shared.LogLevel.ERROR,
                        function_name = "PollVoteView.vote_button",
                        description = f"Failed to edit poll message: {e}"
                    )

        # Acknowledge to the voter (ephemeral)
        await interaction.response.send_message(f"You voted for **{self.selected_option}**.", ephemeral=True)

        # Reset selection so the user must actively pick next time
        self.selected_option = None
        # Reset the selector displayed value
        try:
            self.selector.values = []
        except Exception:
            pass

class Poll(commands.Cog):
    poll_views: dict[int, PollCreationView] = {}
    
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
        view.setup_interaction = interaction
        await interaction.response.send_message(embed = embed, view = view, ephemeral = True)

    @app_commands.command(name = "yumepollend", description = "End an existing poll")
    async def end_poll(self, interaction: discord.Interaction, poll_id: int) -> None:
        if await polls_service.end_poll(poll_id, interaction.user.id, interaction.guild_id):
            if Poll.poll_views.get(poll_id) is None:
                    return
            
            poll_view = Poll.poll_views[poll_id]
            new_embed = poll_view.public_message.embeds[0]
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
            options_votes = []
            for option, votes in poll_model.votes.items():
                options_votes.append((option, len(votes)))

            new_embed.set_field_at(
                field_index,
                name = new_embed.fields[field_index].name,
                value = "\n".join(
                    f"`{option}` (votes: {votes}){'\nVoters: ' + ', '.join(f'<@{voter}>' for voter in poll_model.votes[option])\
                    if not poll_view.anonymous_voting else ''}" for option, votes in options_votes
                ),
                inline = new_embed.fields[field_index].inline
            )
            # Add the anonymity field
            new_embed.add_field(name = "Anonymous Voting", value = "Enabled" if poll_view.anonymous_voting else "Disabled", inline = False)
            # Set color to red to indicate ended poll status
            new_embed.color = discord.Color.red()
            # Edit the original message to reflect ended poll status
            message = poll_view.public_message
            await message.edit(embed = new_embed, view = None)
            Poll.poll_views.pop(poll_model.poll_id, None)
            
            await interaction.response.send_message(
                content = "Poll ended successfully.",
                ephemeral = True,
                #delete_after = 3
            )
        else:
            await interaction.response.send_message(
                content = "Failed to end Poll. Something went wrong...",
                ephemeral = True,
                delete_after = 3
            )

    @app_commands.command(name = "yumepolls", description = "See all your active polls")
    async def show_active_polls(self, interaction: discord.Interaction, user: discord.User = None) -> None:        
        user_id = interaction.user.id if not user else user.id

        polls = await polls_service.get_active_polls(user_id, interaction.guild_id)
        if polls:
            embed = helpers.embed_generator(
                title = f"Active Polls for {shared.SHIRAYUME.get_user(user_id)}",
                description = "",
                color = (128, 0, 128)
            )

            for poll in polls:
                poll_view = Poll.poll_views.get(poll.poll_id, None)

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

                options_votes = []
                for option, votes in poll.votes.items():
                    options_votes.append((option, len(votes)))

                embed.add_field(
                    name = "Results",
                    value = "\n".join(
                    f"`{option}` (votes: {votes}){'\nVoters: ' + ', '.join(f'<@{voter}>' for voter in poll.votes[option])\
                    if not poll_view.anonymous_voting else ''}" for option, votes in options_votes
                    ),
                    inline = False
                )
                # Add anonymity field
                embed.add_field(
                    name = "Anonymous Voting",
                    value = "Enabled" if poll_view.anonymous_voting else "Disabled",
                    inline = False
                )

            await interaction.response.send_message(
                embed = embed,
                ephemeral = True
            )
        else:
            await interaction.response.send_message(
                content = f"User {shared.SHIRAYUME.get_user(user_id)} doesn't have any active polls.",
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

            # Update the votes in the embed while we're at it & show voters if not anonymous
            field_index = 1
            options_votes = []
            for option, votes in poll_model.votes.items():
                options_votes.append((option, len(votes)))

            new_embed.set_field_at(
                field_index,
                name = new_embed.fields[field_index].name,
                value = "\n".join(
                    f"`{option}` (votes: {votes}){'\nVoters: ' + ', '.join(f'<@{voter}>' for voter in poll_model.votes[option])\
                    if not poll_view.anonymous_voting else ''}" for option, votes in options_votes
                ),
                inline = new_embed.fields[field_index].inline
            )
            # Add the anonymity field
            new_embed.add_field(name = "Anonymous Voting", value = "Enabled" if poll_view.anonymous_voting else "Disabled", inline = False)
            # Set color to green to indicate active poll status
            new_embed.color = discord.Color.green()
            # Edit the original message to reflect updated poll status
            message = poll_view.public_message
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
    async def cancel_vote(self, interaction: discord.Interaction, poll_id: int) -> None:
        if await polls_service.cancel_vote_poll(poll_id, interaction.guild_id, interaction.user.id):
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

async def setup() -> None:
    await shared.SHIRAYUME.add_cog(Poll(), override=True)
