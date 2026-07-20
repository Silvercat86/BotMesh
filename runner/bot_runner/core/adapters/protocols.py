from typing import Protocol


class BotAdapter(Protocol):
    
    async def send(
        self,
        chat_id: int,
        text: str,
        photo: str | None = None
    ) -> None: ...

    async def reply(
        self,
        message,
        text: str,
        photo: str | None = None
    ) -> None: ...

    

    