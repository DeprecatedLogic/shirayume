import sys
from colorama import init
init(strip=not sys.stdout.isatty()) # strip colors if stdout is redirected
from termcolor import cprint
from pyfiglet import figlet_format

def custom_format(text: str, font: str = "big", attributes: list = ['bold']) -> None:
    cprint(figlet_format(text, font=font), attrs=attributes)