from random import randint

class NumberGame:
        def __init__(self, user_id: int, from_number: int, to_number: int, attempts: int):
            self.user_id = user_id
            self.from_number = from_number
            self.to_number = to_number
            self.attempts_left = attempts
            self.answer = randint(from_number, to_number)
            self.guesses: list[int] = []

        def make_guess(self, value: int) -> str:
            self.guesses.append(value)
            self.attempts_left -= 1
            if value == self.answer:
                return "win"
            if value < self.answer:
                return "bigger"
            return "smaller"

        def out_of_attempts(self) -> bool:
            return self.attempts_left <= 0

        def summary(self) -> str:
            g = ", ".join(str(x) for x in self.guesses[-10:]) if self.guesses else "—"
            return f"Attempts left: {self.attempts_left}\nRecent guesses: {g}"