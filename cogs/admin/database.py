from discord.ext import tasks, commands
from database import database_manager
from utils import shared, helpers

class BackupManager(commands.Cog):
    def __init__(self) -> None:
        self.auto_commit_loop.start()

    def cog_unload(self) -> None:
        """Ensures the background task is terminated when the cog unloads."""
        self.auto_commit_loop.cancel()

    @tasks.loop(minutes=2.0)
    async def auto_commit_loop(self) -> None:
        """Periodically flushes tracking changes to database layers."""
        await database_manager.DB_MANAGER.database_commit()

    @auto_commit_loop.before_loop
    async def before_commit_loop(self) -> None:
        await shared.SHIRAYUME.wait_until_ready()

    @commands.is_owner()
    @commands.command(name="commit")
    async def force_commit(self, ctx: commands.Context) -> None:
        """Immediately flushes all currently tracked modifications to the database."""
        await database_manager.DB_MANAGER.database_commit()
        await ctx.send("Database state manually committed successfully.")

    @commands.is_owner()
    @commands.command(name="stopcommit")
    async def stop_commit_loop(self, ctx: commands.Context) -> None:
        """Disables the automated database synchronization task."""
        if self.auto_commit_loop.is_running():
            self.auto_commit_loop.cancel()
            await ctx.send("Auto-commit loop has been stopped.")
        else:
            await ctx.send("Auto-commit loop is already offline.")

    @commands.is_owner()
    @commands.command(name="startcommit")
    async def start_commit_loop(self, ctx: commands.Context) -> None:
        """Enables or restarts the automated database synchronization task."""
        if not self.auto_commit_loop.is_running():
            self.auto_commit_loop.start()
            await ctx.send("Auto-commit loop has been started.")
        else:
            await ctx.send("Auto-commit loop is already running.")

async def setup() -> None:
    await shared.SHIRAYUME.add_cog(BackupManager(), override=True)
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        function_name="cogs.admin.database.setup",
        description="Setup completed successfully"
    )