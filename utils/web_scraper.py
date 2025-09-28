import requests
from shared import SupportedWebsites
from bs4 import BeautifulSoup
import re

class WebScraper():

    supported_websites = {
        SupportedWebsites.my_anime_list: re.compile(r"(https://)?(www\.)?myanimelist\.net/(anime|manga)/\d+/\w"),
        SupportedWebsites.brainy_quote: re.compile(r"(https://)?(www\.)?brainyquote\.com/link/quote(br|ar|fu|lo|na)\.js")
    }

    @staticmethod
    def check_url_support(url: str) -> str | None:
        for website, pattern in WebScraper.supported_websites.items():
            if re.match(pattern, url):
                return website
        return None

    @staticmethod
    def get_html_page(url: str) -> tuple[str, BeautifulSoup] | None:
        """ Fetch website's content.

        Parameters
        ----------
        url: The website's URL to scrape data from (str)

        Returns
        -------
        If successful, a `tuple` containing the website's name and the BeautifulSoup object, otherwise `None`.

        Notes
        -----
        Checks if the website is supported before proceeding.
        
        """
        try:
            website_name = WebScraper.check_url_support(url)
            if website_name is None:
                print("[get_html_page] This website is not supported")
                return None
            
            response = requests.get(url)
            
            # Check the status code and handle errors if necessary
            if response.status_code == 200:
                html_content = BeautifulSoup(markup = response.content, features = "html.parser")
                return (website_name, html_content)
            else:
                print(f"[get_html_page] Connection error, bad status code: {response.status_code}")

        except Exception as e:
            print(f"{e}") # for now print exceptions in general, no specifics
            return None

    @staticmethod
    def extract_mal_data(content: BeautifulSoup) -> dict | None:
        """ Extract specific data from website 'MyAnimeList'.

        Parameters
        ----------
        content: HTML content to extract data from (BeautifulSoup)

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

        try:
            if content.find("div", class_ = "breadcrumb").text.find("Anime") != -1:
                data["type"] = "Anime"
            else:
                data["type"] = "Manga"
        except:
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
                        data[field] = ""
        
        # I feel like a genius...
        return data

    @staticmethod
    def extract_brainyquote_data(content: BeautifulSoup) -> dict | None:
        """ Extract specific data from website 'BrainyQuote'.

        Parameters
        ----------
        content: HTML content to extract data from (BeautifulSoup)

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

        These are daily quotes.
        """
        try:
            return {
                'title': content.contents[1].contents[0],
                'author': content.contents[6].contents[0],
                'content': content.contents[3].split('"')[-1]
            }
        except:
            return None
        
    @staticmethod
    def extract_data(website: str, content: BeautifulSoup) -> dict | None:
        """ Extract data from HTML content.

        Parameters
        ----------
        website: The website's name from the WebScraper.supported_websites' keys (str)
        content: HTML content to extract data from (BeautifulSoup)

        Returns
        -------
        A dictionary containing the wanted data based on the website.
        
        Notes
        -----
        There's an API available for MAL but... for now scraping is fine.

        """
        if website is None:
            return None

        data = {}
        data["page_title"] = content.title.text.strip()

        try:
            if website == SupportedWebsites.my_anime_list:
                data["recognized_as"] = SupportedWebsites.my_anime_list
                temp_data = WebScraper.extract_mal_data(content)
                
            elif website == SupportedWebsites.brainy_quote:
                data["recognized_as"] = SupportedWebsites.brainy_quote
                temp_data = WebScraper.extract_brainyquote_data(content)

            if temp_data is not None:
                data.update(temp_data)

        except Exception as e:
            print(f"[extract_data] {e}")