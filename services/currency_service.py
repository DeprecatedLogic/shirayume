class Currency():

    def __init__(self, currency_name: str = "Yumecoin", icon_url: str = "", max_currency: int = 9999999):
        self.currency_name = currency_name
        self.icon_url = icon_url
        self.max_currency = max_currency

    @property
    def max_currency(self) -> int:
        return self._max_currency

    @property.setter
    def max_currency(self, value: int) -> None:
        if type(value) == int and value >= 0:
            self._max_currency = value

    @property
    def icon_url(self) -> str:
        return self._icon_url

    @property.setter
    def icon_url(self, value: str) -> None:
        if type(value) == str and len(value) != None:
            self._icon_url = value
            return
        print(f"[ERROR] Argument of type {type(value)} passed to 'Currency.icon_url' with value: {value}") # placeholder

class Item():

    def __init__(self, name: str, description: str, price: int, is_available: bool = True, is_locked: bool = False):
        self.name = name
        self.description = description
        self.price = price
        self.is_available = is_available
        self.is_locked = is_locked

class Section():

    def __init__(self, name: str, description: str, is_available: bool, is_locked: bool, max_items: int = 999):
        self.name = name
        self.description = description
        self.is_available = is_available
        self.is_locked = is_locked
        self.max_items = max_items
        self.items: list[Item] = []

class Shop():
    total_items = 0
    def __init__(self, items: list | None):
        self.sections: dict[str, Section] = {}

    def add_items(self, items: list[Item], section: str) -> bool:
        if type(items) == list and len(items) > 0:
            size = Shop.total_items
            for item in items:
                if type(item) == Item:
                    self.sections[section].items.append(item)
                    Shop.total_items += 1
            if len(self.sections[section].items) - len(items) == size:
                return True
        return False
