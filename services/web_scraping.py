from utils.shared import SupportedWebsites
from bs4 import BeautifulSoup
import re
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from utils import shared, helpers
from time import time

class Cache():
    """ Handles cache for WebScraper. """

    def __init__(self, entries: dict[str, dict] = {}, duration: int = 86400):
        self._entries = entries
        self.duration = duration
        self._timestamp = time()

    @property
    def duration(self) -> int:
        return self._duration
    
    @duration.setter
    def duration(self, value: int) -> None:
        if type(value) is not int or value < -1:
            raise ValueError("Duration must be an integer greater than or equal to -1.")
        self._duration = value

    @property
    def timestamp(self):
        return self._timestamp

    def update_entries(self, **kwargs) -> None:
        for key, value in kwargs.items():
            self._entries[key] = value
        self._timestamp = time() # self.timestamp is read-only, use internal variable
    
    def clear_entry(self, *keys) -> None:
        for key in keys:
            self._entries.pop(key, default = None) # set default to avoid exceptions

    def get_entries(self) -> dict[str, dict]:
        return self._entries
    
    def is_outdated(self) -> bool:
        """ Checks if cache is outdated based on duration.
        
        Returns
        -------
        `True` when there's a difference of `self.duration` between current time
        and last cache update or `self.duration` is -1, otherwise False.
        
        Notes
        -----
        - If self.duration is -1, cache persists unless manually cleaned.
        - If self.duration is 0, cache will always be updated rendering the implementation useless...
        
        """
        return self.duration != -1 and time() - self.duration >= self.timestamp


class WebScraper():
    thread_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers = 3) # by default a max of 3 threads
    _brainyquote_cache: Cache = Cache() # <quote_type>, <data>
    _mal_cache: Cache = Cache() # <type_&_id>, <data>

    supported_websites = {
        SupportedWebsites.my_anime_list: re.compile(r"(https://)?(www\.)?myanimelist\.net/(anime|manga)/\d+/\w"),
        SupportedWebsites.brainy_quote: re.compile(r"(https://)?(www\.)?brainyquote\.com/link/quote(br|ar|fu|lo|na)\.js")
    }

    @classmethod
    def check_url_support(cls, url: str) -> str | None:
        """ Returns the website's name if the URL is supported.
        
        Parameters
        ----------
        url: The website's URL to check (str)

        Returns
        -------
        If successful, the website's name (`str`), otherwise `None`.
        
        """
        for website, pattern in cls.supported_websites.items():
            if re.match(pattern, url):
                return website
        return None

    @classmethod
    async def get_html_page(cls, url: str) -> tuple[str, str] | None:
        """ Fetch website's content.

        Parameters
        ----------
        url: The website's URL to scrape data from (str)

        Returns
        -------
        If successful, a `tuple` containing the website's name and the html content, otherwise `None`.

        Notes
        -----
        Checks if the website is supported before proceeding.
        
        """
        try:
            website_name = cls.check_url_support(url)
            if website_name is None:
                helpers.custom_print(
                    level = shared.LogLevel.DEBUG,
                    function_name = "get_html_page",
                    description = f"An unsupported URL ({url}) was passed as an argument"
                )
                return None

            if website_name == SupportedWebsites.my_anime_list:
                if not cls._mal_cache.is_outdated() and url in cls._mal_cache:
                    return cls._mal_cache.get_data().get(url, default = None)
            elif website_name == SupportedWebsites.brainy_quote:
                if not cls._brainyquote_cache.is_outdated() and url in cls._brainyquote_cache:
                    return cls._brainyquote_cache.get_data().get(url, default = None)

            # website_name is valid and data is not cached
            # so make a request
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    # Check the status code and handle errors if necessary
                    if response.status == 200:
                        html_content = await response.text()
                        return (website_name, html_content)
                    else:
                        helpers.custom_print(
                            level = shared.LogLevel.ERROR,
                            function_name = "get_html_page",
                            description = f"Connection error, bad status code: {response.status}"
                        )
        except Exception as e:
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "get_html_page",
                description = f"An error occured: {e}"
            )
            return None

    @staticmethod
    def extract_mal_results(content: str) -> dict | None:
        """ Extract the data of the search results from the website 'MyAnimeList'.
        
        Parameters
        ----------
        content: HTML content to extract data from (str)

        Returns
        -------
        A `dict` containing the results, Anime/Manga probably.

        In case of failure, `None`.
        
        """

    @staticmethod
    def extract_mal_data(content: str) -> dict | None:
        """ Extract specific data from the website 'MyAnimeList'.

        Parameters
        ----------
        content: HTML content to extract data from (str)

        Returns
        -------
        A `dict` containing the wanted data from the 'MyAnimeList' website.

        Keys:
        - type
        - japanese_title
        - english_title
        - description
        - image_url
        - synonyms
        - japanese
        - english
        - episodes
        - chapters
        - status
        - aired
        - published
        - genres
        - themes

        In case of failure, `None`.

        """
        data = {}

        # Create an object of BeautifulSoup out of the HTML content
        content: BeautifulSoup = BeautifulSoup(markup = content, features = "html.parser")

        data["page_title"] = content.title.text.strip() if content.title else ""
        data["website_recognized_as"] = SupportedWebsites.my_anime_list

        # Extract the basic info that defines the data
        try:
            if content.find("div", class_ = "breadcrumb").text.find("Anime") != -1:
                data["type"] = "Anime"
            else:
                data["type"] = "Manga"
        except Exception as e:
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "extract_mal_data",
                description = f"An error occured: {e}"
            )
            return None
        
        if data["type"] == "Anime":
            name_div = content.find("div", itemprop = "name")
            data["japanese_title"] = name_div.find("h1", class_ = "title-name h1_bold_none").strong.text
            data["description"] = content.find("p", itemprop = "description").text
            try:
                data["english_title"] = name_div.find("p", class_ = "title-english title-inherit").text    
            except:
                data["english_title"] = ""

        elif data["type"] == "Manga":
            name_div = content.find("span", class_ = "h1-title")
            data["japanese_title"] = name_div.find("span", itemprop = "name").text
            data["description"] = content.find("span", itemprop = "description").text
            try:
                data["english_title"] = name_div.find("span", class_ = "title-english").text    
            except:
                data["english_title"] = ""

        data["description"] = ' '.join(data["description"].split())

        # Extract the image URL
        left_side_div = content.find("div", class_ = "leftside")
        data["image_url"] = left_side_div.find("a").find("img")["data-src"]

        # First, define an extraction pattern for each field to avoid duplication
        # Old me had 50 lines of spaghetti code, today, I'm a better version of myself! (lol)
        extraction_rules = {
            'Synonyms': ('synonyms', lambda text: '|'.join(text.split(': ', 1)[1].split(', '))),
            'Japanese': ('japanese', lambda text: '|'.join(text.split(': ', 1)[1].split(', '))),
            'English': ('english', lambda text: '|'.join(text.split(': ', 1)[1].split(', '))),
            'Episodes': ('episodes', lambda text: text.split(':\n  ')[1]),
            'Chapters': ('chapters', lambda text: text.split(': ', 1)[1]),
            'Status': ('status', lambda text, item_type: text.split(':\n  ')[1] if item_type == 'Anime' else text.split(': ')[1]),
            'Aired': ('aired', lambda text: '|'.join(text.split(':\n  ')[1].split(' to '))),
            'Published': ('published', lambda text: '|'.join(text.split(': ')[1].split(' to '))),
            'Genres': ('genres', lambda row, item_type: '|'.join(
                genre.text.strip() for genre in row.find_all('span', itemprop='genre', 
                style='display: none' if item_type == 'Anime' else 'display:none')
            )),
            'Themes': ('themes', lambda row, item_type: '|'.join(
                theme.text.strip() for theme in row.find_all('span', itemprop='genre', 
                style='display: none' if item_type == 'Anime' else 'display:none')
            ))
        }

        # Extract the rest of the information about the Anime/Manga
        for row in content.find_all("div", class_ = "spaceit_pad"):
            row_text = row.text.strip()

            for keyword, (field, extract_func) in extraction_rules.items():
                if keyword in row_text:
                    try:
                        if keyword in ("Status", "Genres", "Themes"):
                            if keyword == "Status":
                                data[field] = extract_func(row_text, data["type"])
                            else:
                                data[field] = extract_func(row, data["type"])
                        else:
                            data[field] = extract_func(row_text)
                    except (IndexError, KeyError):
                        data[field] = "" # stopping = wasted resources, better empty value and continue
        
        # I feel like a genius...
        cache_entry = {data["page_title"]: data}
        WebScraper._mal_cache.update_entries(cache_entry)
        return data

    @staticmethod
    def extract_brainyquote_data(content: str) -> dict | None:
        """ Extract specific data from website 'BrainyQuote'.

        Parameters
        ----------
        content: HTML content to extract data from (str)

        Returns
        -------
        A dictionary containing the wanted data from the 'BrainyQuote' website.
        
        Keys:
        - title
        - author
        - content

        In case of failure, `None`.
        
        Notes
        -----
        Currently available BrainyQuote URLS are:
        - "https://www.brainyquote.com/link/quotebr.js",
        - "https://www.brainyquote.com/link/quotear.js",
        - "https://www.brainyquote.com/link/quotefu.js",
        - "https://www.brainyquote.com/link/quotelo.js",
        - "https://www.brainyquote.com/link/quotena.js"

        These are daily quotes. Yes, they are js files, I know.

        """
        try:
            data = {}

            # Create an object of BeautifulSoup out of the HTML content
            content: BeautifulSoup = BeautifulSoup(markup = content, features = "html.parser")

            data["page_title"] = content.title.text.strip() if content.title else ""
            data["website_recognized_as"] = SupportedWebsites.brainy_quote
            data.update(
                title = content.contents[1].contents[0],
                author = content.contents[6].contents[0],
                content = content.contents[3].split('"')[-1]
            )
            cache_entry = {data["page_title"]: data}
            WebScraper._brainyquote_cache.update_entries(cache_entry)
            return data
        except Exception as e:
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "extract_brainyquote_data",
                description = f"An error occured: {e}"
            )
            return None
