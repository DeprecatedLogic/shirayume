import discord
from discord import app_commands
from discord.ext import commands
from services.web_scraping import WebScraper
from utils import shared, helpers
from random import choice

class WebScraping(commands.Cog):

    @app_commands.command(name = "dailyquote", description = "Get a quote from BrainyQuote (updated daily)")
    async def daily_quote(self, interaction: discord.Interaction):
        try:
            brainyquote_urls = [
                "https://www.brainyquote.com/link/quotebr.js",
                "https://www.brainyquote.com/link/quotear.js", 
                "https://www.brainyquote.com/link/quotefu.js",
                "https://www.brainyquote.com/link/quotelo.js",
                "https://www.brainyquote.com/link/quotena.js"
            ]
            url = choice(brainyquote_urls)

            website_content_pair = await WebScraper.get_html_page(url)
            if website_content_pair is not None:
                website, content = website_content_pair
                extracted_data = WebScraper.extract_brainyquote_data(content)
                formatted_description = f"{extracted_data['content']} - {extracted_data['author']}"
                embed = helpers.embed_generator(
                    title = extracted_data['title'],
                    description = formatted_description
                )
                await interaction.response.send_message(embed = embed)
        except discord.Forbidden:
            embed = helpers.embed_generator(
                title = "Daily Quote",
                description = "You don't have sufficient permission to execute this command."
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)

        except Exception as e:
            embed = helpers.embed_generator(
                title = "Daily Quote",
                description = "I failed to fetch a daily quote for you... sorry!",
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "daily_quote",
                description = f"An error occured: {e}"
            )

    # WARNING: Do not use, does not work yet
    @app_commands.command(name = "mal", description = "Get info for a specific anime/manga (usually up-to-date lol)")
    async def mal(self, interaction: discord.Interaction, title: str, manga: bool = False):
        try:
            # todo: search and let the user pick from the results
            url = f"https://myanimelist.net/search/all?cat=all&q={title}"
            # todo: use the URL of the item that the user picked
            website_content_pair = await WebScraper.get_html_page(url)
            if website_content_pair is not None:
                website, content = website_content_pair
                extracted_data = await helpers.exec_in_thread(
                    WebScraper.thread_pool,
                    WebScraper.extract_mal_data,
                    content
                )
                # todo: format description and fix embed below
                formatted_description = f""
                embed = helpers.embed_generator(
                    title = extracted_data['title'],
                    description = formatted_description
                )
                await interaction.response.send_message(embed = embed)
        except discord.Forbidden:
            embed = helpers.embed_generator(
                title = "MAL",
                description = "You don't have sufficient permission to execute this command."
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)

        except Exception as e:
            embed = helpers.embed_generator(
                title = "MAL",
                description = f"I failed to fetch the data for `{title}`... sorry!",
            )
            await interaction.response.send_message(embed = embed, ephemeral = True)
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "mal",
                description = f"An error occured: {e}"
            )

async def setup():
    if "WebScraping" not in shared.SHIRAYUME.cogs:
        await shared.SHIRAYUME.add_cog(WebScraping())