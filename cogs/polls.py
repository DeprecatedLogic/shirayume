import datetime as dt
from datetime import datetime
from services import polls as polls_service
import discord
from discord.ui import View, Button, TextInput
from discord import app_commands
from discord.ext import commands
from utils import shared, helpers
from typing import Union, Optional, List, Any
from database import models
import asyncio

def _format_poll_options(votes: dict[str, list[int]]) -> str:
    """
    Formats the poll options and their respective vote counts into a scannable string.

    Args:
        votes (dict[str, list[int]]): A mapping of options to lists of voter IDs.

    Returns:
        str: A formatted string representing the poll options.
    """
    if len(votes) == 0:
        return "No Options"

    # Display the current vote count for every configured option
    return "\n".join(
        f"`{option}` ({len(voters)} votes)"
        for option, voters in votes.items()
    )

async def _sleep_and_close_poll(poll: models.Poll) -> None:
    """
    Calls the service `sleep_and_close_poll` function which sleeps until a poll reaches its expiration time  
    and automatically handles its closure.

    Its Discord message is refreshed to reflect the closed state.

    Args:
        poll (models.Poll): _description_
    """
    await polls_service.sleep_and_close_poll(poll)

    # Wait until the bot is fully connected and internal caches are populated
    await shared.SHIRAYUME.wait_until_ready()

    await update_poll_message(poll)

async def update_poll_message(poll_model: models.Poll, message: Optional[discord.Message] = None) -> None:
    """
    Utility function to dynamically refresh the embed components and view states of a poll message.

    Args:
        poll_model (models.Poll): The poll data model to retrieve status from.
        message (Optional[discord.Message]): An optional existing message object to edit.
    """
    if not message:
        guild = shared.SHIRAYUME.get_guild(poll_model.guild_id)
        if not guild:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Unable to refresh poll {poll_model.poll_id}: guild not found."
            )
            return
        try:
            channel = guild.get_channel(poll_model.channel_id) or await guild.fetch_channel(poll_model.channel_id)
            if not channel:
                helpers.custom_print(
                    level=shared.LogLevel.DEBUG,
                    description=f"Unable to refresh poll {poll_model.poll_id}: channel not found."
                )
                return
            message = await channel.fetch_message(poll_model.message_id)
        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Unable to fetch poll message {poll_model.poll_id}: {e}"
            )

    if not message or not message.embeds:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Unable to refresh poll {poll_model.poll_id}: message or its embeds not found."
        )
        return

    embed = message.embeds[0]
    unix_timestamp = int(poll_model.ends_at.timestamp())
    
    edit_kwargs: dict[str, Any] = {"embed": embed}
    
    if poll_model.is_active:
        status = f"Ends <t:{unix_timestamp}:R>"
        embed.color = discord.Color.green()
    else:
        status = f"Ended: <t:{unix_timestamp}:F>"
        embed.color = discord.Color.red()
        edit_kwargs["view"] = None

    embed.clear_fields()
    embed.add_field(name="Status", value=status, inline=False)
    embed.add_field(name="Options", value=_format_poll_options(poll_model.votes), inline=False)
    
    is_anonymous = "Enabled"
    for field in message.embeds[0].fields:
        if field.name == "Anonymous Voting":
            is_anonymous = field.value
            break
            
    embed.add_field(name="Anonymous Voting", value=is_anonymous, inline=False)
    embed.add_field(name="Poll ID", value=str(poll_model.poll_id), inline=True)

    try:
        await message.edit(**edit_kwargs)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Updated poll message for poll {poll_model.poll_id}."
        )
    except Exception as e:
        helpers.custom_print(
            level=shared.LogLevel.ERROR,
            description=f"Failed to edit poll message: {e}"
        )

class PollCreationView(View):
    """
    An interactive UI view handling the configuration and creation stage of a poll.

    Args:
        question (str): The poll question.
        embed (Union[discord.Embed, None]): The preview embed.
        timeout (int): Timeout duration for the view.
    """

    def __init__(self, question: str, embed: Union[discord.Embed, None], timeout: int = 180) -> None:
        super().__init__(timeout=timeout)
        self.question = question
        self.embed = embed
        self.options: List[str] = []
        
        self.duration_days = 0
        self.duration_hours = 0
        self.duration_minutes = 0
        self.duration_seconds = 0
        
        self.setup_interaction: Optional[discord.Interaction] = None
        self.poll_model: Optional[Poll] = None
        self.anonymous_voting = True

    async def on_timeout(self) -> None:
        """
        Handles view timeout by cleaning up the setup interaction response.
        """
        try:
            if self.setup_interaction:
                await self.setup_interaction.delete_original_response()
        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Failed to delete poll setup message: {e}"
            )

    @discord.ui.button(label="Set Options", style=discord.ButtonStyle.primary)
    async def set_options(self, interaction: discord.Interaction, button: Button) -> None:
        """
        Triggers the modal to define poll options.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button pressed.
        """
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"{interaction.user.id} opened poll option configuration."
        )
        await interaction.response.send_modal(PollOptionsModal(self))

    @discord.ui.button(label="Set Duration", style=discord.ButtonStyle.primary)
    async def set_duration(self, interaction: discord.Interaction, button: Button) -> None:
        """
        Triggers the modal to define poll duration.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button pressed.
        """
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"{interaction.user.id} opened poll duration configuration."
        )
        await interaction.response.send_modal(PollDurationModal(self))

    @discord.ui.button(label="Anonymous Voting: ON", style=discord.ButtonStyle.green)
    async def anonymity_toggle(self, interaction: discord.Interaction, button: Button) -> None:
        """
        Toggles anonymity status of the poll.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button pressed.
        """
        self.anonymous_voting = not self.anonymous_voting
        if self.anonymous_voting:
            button.label = "Anonymous Voting: ON"
            button.style = discord.ButtonStyle.green
            self.embed.set_footer(text="Anonymous Voting: Enabled")
        else:
            button.label = "Anonymous Voting: OFF"
            button.style = discord.ButtonStyle.red
            self.embed.set_footer(text="Anonymous Voting: Disabled")

        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"{interaction.user.id} toggled poll anonymity "
                f"({'ON' if self.anonymous_voting else 'OFF'})."
            )
        ) 
        await interaction.response.edit_message(embed=self.embed, view=self)
    
    @discord.ui.button(label="Create Poll", style=discord.ButtonStyle.green)
    async def create_poll(self, interaction: discord.Interaction, button: Button) -> None:
        """
        Finalizes poll configuration and pushes it to the service.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button pressed.
        """
        if not self.question: # This should normally never happen
            await interaction.response.send_message(
                content="Something went wrong, no question was found.",
                ephemeral=True, delete_after=10
            )
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description="No question was found when trying to create a poll ?!"
            )
            return
        
        if not self.options or not all(opt.strip() for opt in self.options):
            await interaction.response.send_message(
                content="Please set all options.",
                ephemeral=True, delete_after=5
            )
            return
            
        if (self.duration_days + self.duration_hours + self.duration_minutes + self.duration_seconds) == 0:
            await interaction.response.send_message(
                content="Please set a duration for the poll.",
                ephemeral=True, delete_after=5
            )
            return
        
        datetime_now = datetime.now()
        ends_at_datetime = datetime_now + dt.timedelta(
            days=self.duration_days,
            hours=self.duration_hours,
            minutes=self.duration_minutes,
            seconds=self.duration_seconds
        )

        self.poll_model = await polls_service.create_poll(
            guild_id=interaction.guild_id,
            creator_id=interaction.user.id,
            question=self.question,
            votes={str(option): [] for option in self.options},
            is_active=True,
            is_anonymous=self.anonymous_voting,
            created_at=datetime_now,
            updated_at=datetime_now,
            ends_at=ends_at_datetime,
            is_dirty=True,
            message_id=-1,
            channel_id=-1
        )

        if not self.poll_model:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description="Poll creation failed in service."
            )
            await interaction.response.send_message(
                content="Failed to create poll, something went wrong.",
                ephemeral=True, delete_after=10
            )
            return

        new_embed = helpers.embed_generator(
            title=self.question,
            description="",
        )
        status = f"Ends <t:{int(ends_at_datetime.timestamp())}:R>"
        
        new_embed.add_field(name="Status", value=status, inline=False)
        new_embed.add_field(name="Options", value=_format_poll_options(self.poll_model.votes), inline=False)
        new_embed.add_field(name="Anonymous Voting", value="Enabled" if self.anonymous_voting else "Disabled", inline=False)
        new_embed.add_field(name="Poll ID", value=str(self.poll_model.poll_id), inline=True)
        
        new_embed.set_footer(
            text=f"Created by {interaction.user.name}",
            icon_url=interaction.user.display_avatar
        )
        new_embed.color = discord.Color.green()

        self.embed = new_embed
        vote_view = PollVoteView(self.poll_model)

        try:
            await interaction.response.send_message(embed=new_embed, view=vote_view)
            self.stop()
            
            public_message = await interaction.original_response()
            self.poll_model.message_id = public_message.id
            self.poll_model.channel_id = public_message.channel.id
            polls_service.poll_modified(self.poll_model)
            interaction.client.add_view(vote_view)
            helpers.custom_print(level=shared.LogLevel.DEBUG, description=f"Poll {self.poll_model.poll_id} successfully deployed.")
        except Exception as e:
            await polls_service.end_poll(
                self.poll_model.poll_id,
                self.poll_model.creator_id,
                self.poll_model.guild_id
            )
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Failed to deploy live poll interface: {e}"
            )
            return
            
        try:
            if self.setup_interaction:
                await self.setup_interaction.delete_original_response()
        except Exception:
            pass

        asyncio.create_task(_sleep_and_close_poll(poll=self.poll_model))

class PollOptionsModal(discord.ui.Modal):
    """
    Modal allowing users to configure the available options for a poll.

    Args:
        view (PollCreationView): The parent creation view.
    """

    def __init__(self, view: PollCreationView) -> None:
        super().__init__(title="Enter Poll Options")
        self.view = view

        self.options_input = TextInput(
            label="Options (One per line, Max 25)",
            style=discord.TextStyle.paragraph,
            placeholder="Option 1\nOption 2\n...",
            required=True,
            max_length=3000 # 4000 is the limit but... who's crazy enough to reach 3000 anyways ?
        )
        self.add_item(self.options_input)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Processes submitted options and updates the view.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        raw_lines = self.options_input.value.split('\n')
        self.view.options = [line.strip() for line in raw_lines if line.strip()][:25]

        if len(self.view.options) < 2:
            await interaction.response.send_message(
                content="You must provide at least 2 options.",
                ephemeral=True,
                delete_after=10
            )
            return

        new_embed = helpers.embed_generator(
            title=self.view.question,
            description="Poll Options Set!",
        )

        options_text = "\n".join(
            f"{i+1}. {option} (0 votes)"
            for i, option in enumerate(self.view.options)
        )
        new_embed.add_field(name="Options", value=options_text, inline=False)

        if (
            self.view.duration_days + self.view.duration_hours +
            self.view.duration_minutes + self.view.duration_seconds
        ) > 0:
            new_embed.add_field(
                name="Duration",
                value=(
                    f"{self.view.duration_days:2} days {self.view.duration_hours:2} hours "
                    f"{self.view.duration_minutes:2} minutes {self.view.duration_seconds:2} seconds"
                ),
                inline=False
            )
            new_embed.add_field(name="Next Step:", value="Click **Create Poll**", inline=True)
        else:
            new_embed.add_field(name="Next Step:", value="Click **Set Duration**", inline=True)

        new_embed.set_footer(text=f"Anonymous Voting: {'Enabled' if self.view.anonymous_voting else 'Disabled'}")
        self.view.embed = new_embed
        
        await interaction.response.edit_message(embed=new_embed, view=self.view)

class PollDurationModal(discord.ui.Modal):
    """
    Modal allowing users to configure the poll duration.

    Args:
        view (PollCreationView): The parent creation view.
    """
    days = TextInput(label="Days (0-90)", default="0", max_length=2)
    hours = TextInput(label="Hours (0-23)", default="0", max_length=2)
    minutes = TextInput(label="Minutes (0-59)", default="0", max_length=2)
    seconds = TextInput(label="Seconds (0-59)", default="0", max_length=2)

    def __init__(self, view: PollCreationView) -> None:
        super().__init__(title="Set Poll Duration")
        self.view = view
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Parses and validates the input duration.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
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
                    content="Invalid duration. Use 0-90 days, 0-23 hours, 0-59 minutes, 0-59 seconds",
                    ephemeral=True,
                    delete_after=10
                )
                return
            
            self.view.duration_days = days
            self.view.duration_hours = hours
            self.view.duration_minutes = minutes
            self.view.duration_seconds = seconds
            
            new_embed = helpers.embed_generator(
                title=self.view.question,
                description="Poll Duration Set!",
            )
            
            options_text = "\n".join(
                f"{i+1}. {opt or '*empty*'} (0 votes)"
                for i, opt in enumerate(self.view.options)
            ) if self.view.options else "No options set yet."

            new_embed.add_field(name="Options", value=options_text, inline=False)
            new_embed.add_field(
                name="Duration:",
                value=(
                    f"{str(days)+' days ' if days>0 else ''}"
                    f"{str(hours)+' hours ' if hours>0 else ''}"
                    f"{str(minutes)+' minutes ' if minutes>0 else ''}"
                    f"{str(seconds)+' seconds' if seconds>0 else ''}"
                ).strip(),
                inline=False
            )
            
            new_embed.add_field(
                name="Next Step:",
                value="Click **Create Poll**" if self.view.options else "Click **Set Options**",
                inline=False
            )

            new_embed.set_footer(text=f"Anonymous Voting: {'Enabled' if self.view.anonymous_voting else 'Disabled'}")
            self.view.embed = new_embed
            await interaction.response.edit_message(embed=new_embed, view=self.view)
            
        except ValueError:
            await interaction.response.send_message(
                content="Enter valid numbers for duration.",
                ephemeral=True,
                delete_after=10
            )

class EphemeralPollSelector(discord.ui.Select):
    """
    Select menu for choosing an option in a poll.

    Args:
        poll_model (models.Poll): The poll data model.
    """
    def __init__(self, poll_model: models.Poll):
        self.poll_model = poll_model

        super().__init__(
            placeholder="Choose an option...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=opt, value=opt)
                for opt in poll_model.votes.keys()
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        """
        Handles selection callback.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        self.view.selected_option = self.values[0]
        
        for option in self.options:
            option.default = option.value == self.values[0]
        
        await interaction.response.edit_message(content=None, view=self.view)

class ConfirmVoteButton(discord.ui.Button):
    """
    Button to confirm the vote.
    """
    def __init__(self):
        super().__init__(
            label="Confirm Vote",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        """
        Handles vote confirmation logic.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        view: "EphemeralVoteView" = self.view

        if view.selected_option is None:
            await interaction.response.send_message(
                "Choose an option first.",
                ephemeral=True,
                delete_after=10
            )
            return

        if not await polls_service.vote_poll(
            poll_id=view.poll_model.poll_id,
            guild_id=view.poll_model.guild_id,
            user_id=interaction.user.id,
            option=view.selected_option
        ):
            await interaction.response.send_message(
                "Unable to register your vote, the poll may have ended.",
                ephemeral=True,
                delete_after=10
            )
            return

        await update_poll_message(
            view.poll_model,
            message=view.public_message
        )

        await interaction.response.edit_message(
            content=f"You voted for **{view.selected_option}**.",
            view=None,
            delete_after=10
        )

class EphemeralVoteView(discord.ui.View):
    """
    Ephemeral view for handling private voting interactions.

    Args:
        poll_model (models.Poll): The poll model.
        public_message (discord.Message): The public message to update.
    """
    def __init__(self, poll_model: models.Poll, public_message: discord.Message):
        super().__init__(timeout=120)

        self.poll_model: models.Poll = poll_model
        self.public_message: discord.Message = public_message
        self.selected_option: Optional[str] = None

        self.add_item(EphemeralPollSelector(poll_model))
        self.add_item(ConfirmVoteButton())

class PollVoteView(discord.ui.View):
    """
    Discord UI view displayed on public poll messages.  
    Provides the persistent Vote button used to open the ephemeral voting interface.

    Args:
        poll_model (models.Poll): The poll model.
    """

    def __init__(self, poll_model: models.Poll) -> None:
        super().__init__(timeout=None)
        self.poll_model = poll_model
        self.vote_button.custom_id = f"polls:vote:{poll_model.poll_id}"
        self.cancel_vote_button.custom_id = f"polls:cancel_vote:{poll_model.poll_id}"

    @discord.ui.button(label="Vote", style=discord.ButtonStyle.success)
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Triggers the ephemeral voting interface.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button pressed.
        """
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"{interaction.user.id} opened ephemeral poll voting."
        )
        await interaction.response.send_message(
            view=EphemeralVoteView(
                self.poll_model,
                interaction.message
            ),
            ephemeral=True,
            delete_after=30
        )

    @discord.ui.button(label="Cancel Vote", style=discord.ButtonStyle.red)
    async def cancel_vote_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Cancels user's vote.

        Args:
            interaction (discord.Interaction): The interaction object.
            button (discord.ui.Button): The button pressed.
        """
        response = await polls_service.cancel_vote_poll(self.poll_model, interaction.user.id)
        if response["success"]:
            if response.get("has_voted", False):
                await update_poll_message(self.poll_model)
                await interaction.response.send_message(
                    content="You canceled your vote.",
                    ephemeral=True,
                    delete_after=10
                )
                helpers.custom_print(
                    level=shared.LogLevel.DEBUG,
                    description=f"User {interaction.user.id} canceled vote on poll {self.poll_model.poll_id}."
                )
            else:
                await interaction.response.send_message(
                    content="You haven't voted yet.",
                    ephemeral=True,
                    delete_after=10
                )
                helpers.custom_print(
                    level=shared.LogLevel.DEBUG,
                    description=f"User {interaction.user.id} tried to cancel their vote on poll {self.poll_model.poll_id} but hasn't voted yet."
                )
        else:
            await interaction.response.send_message(
                content=(
                    "Failed to cancel your vote. "
                    "Poll may be inactive or might not exist."
                ),
                ephemeral=True,
                delete_after=10
            )

class VoterPaginator(discord.ui.View):
    """
    Cycles through a list of embeds when the voter list exceeds Discord's limits.
    """
    def __init__(self, pages: list[discord.Embed]):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1
        self.page_indicator.label = f"Page {self.current_page + 1}/{len(self.pages)}"

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        
    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass # Purely visual indicator

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

class Poll(commands.Cog):
    """
    Discord cog implementing slash commands and UI interactions related to polls.
    """
    
    @app_commands.command(name="poll", description="Create a new poll")
    async def create_poll(self, interaction: discord.Interaction, question: str) -> None:
        """
        Initiates the poll creation process.

        Args:
            interaction (discord.Interaction): The interaction object.
            question (str): The question for the poll.
        """
        if polls_service.is_limit_reached(interaction.user.id):
            embed = helpers.embed_generator(
                title="Limit Reached",
                description="You have reached the maximum **active** polls allowed.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=10)
            return

        if len(question) == 0 or len(question) > 255:
            embed = helpers.embed_generator(
                title="Max Characters",
                description="Question must have between 1 and 255 characters.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = helpers.embed_generator(
            title=question,
            description="Select options and duration."
        )
        view = PollCreationView(question, embed)
        view.setup_interaction = interaction
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="pollend", description="End an existing poll")
    async def end_poll(self, interaction: discord.Interaction, poll_id: int) -> None:
        """
        Manually ends a poll.

        Args:
            interaction (discord.Interaction): The interaction object.
            poll_id (int): The ID of the poll to end.
        """
        if await polls_service.end_poll(poll_id, interaction.user.id, interaction.guild_id):
            poll = await polls_service.get_poll(poll_id)
            if poll:
                await update_poll_message(poll)
            
            embed = helpers.embed_generator(
                title=f"Poll (ID: {poll_id})",
                description="Poll ended successfully.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
            helpers.custom_print(level=shared.LogLevel.DEBUG, description=f"Poll {poll_id} manually ended.")
        else:
            embed = helpers.embed_generator(
                title=f"Poll (ID: {poll_id})",
                description="Failed to end poll.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=10)

    @app_commands.command(name="activepolls", description="See all your active polls")
    async def show_active_polls(self, interaction: discord.Interaction, user: Optional[discord.User] = None) -> None:
        """
        Lists all active polls for a user.

        Args:
            interaction (discord.Interaction): The interaction object.
            user (Optional[discord.User]): The user to check.
        """
        user_id = interaction.user.id if not user else user.id
        polls = await polls_service.get_active_polls(user_id, interaction.guild_id)
        
        if polls:
            target_user = shared.SHIRAYUME.get_user(user_id) or user or interaction.user
            embed = helpers.embed_generator(
                title=f"Active Polls for {target_user.name}",
                description="",
                color=discord.Color.purple()
            )

            for poll in polls:
                embed.add_field(
                    name=f"[Poll ID {poll.poll_id}]",
                    value=poll.question,
                    inline=False
                )
                unix_timestamp = int(poll.ends_at.timestamp())
                status = f"Open (ends: <t:{unix_timestamp}:F>)"

                embed.add_field(name="Status", value=status, inline=False)
                embed.add_field(name="Results", value=_format_poll_options(poll.votes), inline=False)
                embed.add_field(name="Anonymous Voting", value="Enabled", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            target_name = (shared.SHIRAYUME.get_user(user_id) or user or interaction.user).name
            await interaction.response.send_message(
                content=f"User {target_name} doesn't have any active polls.",
                ephemeral=True,
                delete_after=10
            )
    
    @app_commands.command(name="pollvote", description="Vote for a poll")
    async def vote_poll(self, interaction: discord.Interaction, poll_id: int, option: str) -> None:
        """
        Casts a vote for a poll.

        Args:
            interaction (discord.Interaction): The interaction object.
            poll_id (int): The ID of the poll.
            option (str): The chosen option.
        """
        if await polls_service.vote_poll(poll_id, interaction.guild_id, interaction.user.id, option):
            poll = await polls_service.get_poll(poll_id)
            if poll:
                await update_poll_message(poll)
            await interaction.response.send_message(
                content=f"You voted for option {option}.",
                ephemeral=True,
                delete_after=10
            )
            helpers.custom_print(level=shared.LogLevel.DEBUG, description=f"User {interaction.user.id} voted on poll {poll_id}.")
        else:
            await interaction.response.send_message(
                content="Failed to register your vote, something went wrong.",
                ephemeral=True,
                delete_after=10
            )

    @app_commands.command(name="cancelvote", description="Cancel your vote from a poll")
    async def cancel_vote(self, interaction: discord.Interaction, poll_id: int) -> None:
        """
        Cancels a user's vote.

        Args:
            interaction (discord.Interaction): The interaction object.
            poll_id (int): The ID of the poll.
        """
        poll = await polls_service.get_poll(poll_id)
        response = await polls_service.cancel_vote_poll(poll, interaction.user.id)
        if response["success"]:
            if response.get("has_voted", False):
                await update_poll_message(poll)
                await interaction.response.send_message(
                    content="You canceled your vote.",
                    ephemeral=True,
                    delete_after=10
                )
            else:
                await interaction.response.send_message(
                    content="You have not voted yet.",
                    ephemeral=True,
                    delete_after=10
                )
        else:
            await interaction.response.send_message(
                content=(
                    "Failed to cancel your vote. "
                    "Poll may be inactive or might not exist."
                ),
                ephemeral=True,
                delete_after=10
            )

    @app_commands.command(name="pollvoters", description="Show all users who voted in a specific poll")
    async def poll_voters(self, interaction: discord.Interaction, poll_id: int, target_user: Optional[discord.User] = None) -> None:
        
        poll = await polls_service.get_poll(poll_id)
        
        if not poll:
            await interaction.response.send_message("Poll not found.", ephemeral=True, delete_after=10)
            return
            
        if getattr(poll, 'is_anonymous', True):
            await interaction.response.send_message("This poll is anonymous.", ephemeral=True, delete_after=10)
            return

        # Specific User Check
        if target_user:
            voted_option = next((opt for opt, voters in poll.votes.items() if target_user.id in voters), None)
            
            description = (
                f"<@{target_user.id}> voted for: **{voted_option}**" 
                if voted_option else 
                f"<@{target_user.id}> has not voted in this poll."
            )
            
            embed = helpers.embed_generator(
                title=f"Voter Search: {poll.question}",
                description=description,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Handling ALL Voters with Pagination
        pages: list[discord.Embed] = []
        current_embed = helpers.embed_generator(title=f"Voters: {poll.question}", description=f"Poll ID: {poll.poll_id}")
        field_count = 0
        has_votes = False
        
        for option, voters in poll.votes.items():
            if not voters:
                current_embed.add_field(name=f"{option} (0 votes)", value="*No votes yet.*", inline=False)
                field_count += 1
                continue
                
            has_votes = True
            
            # Format using blockquotes for a cleaner vertical list
            formatted_voters = [f"> <@{uid}>" for uid in voters]
            
            # 40 mentions per field keeps us safely under the 1024 character limit
            chunk_size = 40 
            
            for i in range(0, len(formatted_voters), chunk_size):
                chunk = formatted_voters[i:i + chunk_size]
                value_str = "\n".join(chunk)
                
                # Append a part number to the title if the option exceeds one field
                suffix = f" (pt. {i//chunk_size + 1})" if len(formatted_voters) > chunk_size else ""
                field_name = f"{option}{suffix} ({len(voters)} votes)"
                
                current_embed.add_field(name=field_name, value=value_str, inline=False)
                field_count += 1
                
                # Embeds are limited to 25 fields. If reached, push to pages and start a new embed.
                if field_count == 25:
                    pages.append(current_embed)
                    current_embed = helpers.embed_generator(title=f"Voters: {poll.question} (Cont.)", description=f"Poll ID: {poll.poll_id}")
                    field_count = 0

        if not has_votes:
            current_embed.description = "No one has voted on this poll yet."
            
        if field_count > 0 or not has_votes:
            pages.append(current_embed)

        view = VoterPaginator(pages) if len(pages) > 1 else None
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)

async def setup() -> None:
    """
    Registers the Poll cog, restores persistent poll views, and restarts  
    automatic expiration tasks for active polls during bot startup.
    """
    if shared.GLOBAL_CONFIG["features"]["polls"].get("is_enabled", False):
        await shared.SHIRAYUME.add_cog(Poll(), override=True)
        
        for poll in polls_service.get_all_polls():
            polls_service.ACTIVE_POLLS.setdefault(poll.creator_id, [])
            polls_service.ACTIVE_POLLS[poll.creator_id].append(poll)
            
            view = PollVoteView(poll)
            shared.SHIRAYUME.add_view(view)
            
            asyncio.create_task(_sleep_and_close_poll(poll=poll))
        
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Polls cog setup completed successfully."
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Polls feature is disabled, setup skipped."
        )