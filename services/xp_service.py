class Experience():

    def __init__(self, max_level: int | None, max_xp: int | None):
        self.max_level = max_level if max_level else 100
        self.max_xp = max_xp if max_xp else 9999999 # placeholder
        for level in range(self.max_level):
            xp_value = ... # todo: use the formula to calculate required XP per level
            self.level_xp_relation.append(xp_value)

    @property
    def max_level(self) -> int:
        return self._max_level

    @property.setter
    def max_level(self, value: int) -> None:
        if type(value) == int:
            self._max_level = value

    @property
    def max_xp(self) -> int:
        return self._max_xp

    @property.setter
    def max_xp(self, value: int) -> None:
        if type(value) == int:
            self._max_xp = value

    @property
    def level_xp_relation(self) -> tuple:
        return tuple(self._level_xp_relation) # avoids changes to be applied to the original list

    @property.setter
    def level_xp_relation(self, value: list) -> None:
        self._level_xp_relation = value
