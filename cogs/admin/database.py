from discord.ext import tasks, commands
from database import database_manager
from utils import shared, helpers
from typing import Optional
import asyncio

class AdminDatabase(commands.Cog):
    
    @commands.is_owner()
    @commands.command(name="commit")
    async def force_commit(self, ctx: commands.Context) -> None:
        """Immediately flushes all currently tracked modifications to the database."""
        await database_manager.DB_MANAGER.database_commit()
        await ctx.send("Database state manually committed successfully.")

    @commands.is_owner()
    @commands.command(name="stopdb")
    async def stop_loop_task(self, ctx: commands.Context) -> None:
        """Disables the automated database synchronization task."""
        try:
            msg = await ctx.send("Stopping DB task...")

            task = database_manager.DB_MANAGER.loop_task

            if task is None or task.done():
                await msg.edit(content="DB task is not running.")
                return

            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            await msg.edit(content="DB task stopped.")

        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Failed to stop DB task through commands: {e}"
            )

            try:
                await msg.delete()
            except Exception:
                pass

            await ctx.send("Failed to stop the DB task.")

    @commands.is_owner()
    @commands.command(name="startdb")
    async def start_loop_task(self, ctx: commands.Context) -> None:
        """Enables or restarts the automated database synchronization task."""
        try:
            msg = await ctx.send("Starting DB task...")

            task = database_manager.DB_MANAGER.loop_task

            # Restart existing task if it's still running
            if task is not None and not task.done():
                await msg.edit(
                    content=(
                        "DB task is already running.\n"
                        "Restarting... Please be patient, this might take a while."
                    )
                )
                
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            database_manager.DB_MANAGER.loop_task = asyncio.create_task(
                database_manager.DB_MANAGER._auto_commit_loop()
            )

            await msg.edit(content="DB task started.")

        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Failed to start DB task through commands: {e}"
            )

            try:
                await msg.delete()
            except Exception:
                pass

            await ctx.send("Failed to (re)start the DB task.")

async def setup() -> None:
    await shared.SHIRAYUME.add_cog(AdminDatabase(), override=True)
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description="Admin database cog setup completed successfully."
    )