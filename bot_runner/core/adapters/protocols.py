from typing import Protocol


class BotAdapter(Protocol):
    async def send_text(self, chat_id: int, text: str) -> None: ...
    
    async def send_photo(
        self,
        chat_id: int,
        photo: str,
        caption: str | None = None
    ) -> None: ...