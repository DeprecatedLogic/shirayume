from collections import deque
from utils.shared import MessageDTO

class ConversationManager:
    def __init__(self, history_size: int = 30) -> None:
        self._history_size = history_size
        self._conversations: dict[int, deque[MessageDTO]] = {}

    def add_message(self, message: MessageDTO):
        channel_id = message.channel_id

        if channel_id not in self._conversations:
            self._conversations[channel_id] = deque(maxlen=self._history_size)

        self._conversations[channel_id].append(message)

    def get_history(self, channel_id: int) -> list[dict]:
        if channel_id not in self._conversations:
            return []

        history = self._conversations[channel_id]

        return [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

    def clear_history(self, channel_id: int):
        if channel_id not in self._conversations:
            return
        
        self._conversations[channel_id].clear()

    def clear_all(self):
        self._conversations = {}