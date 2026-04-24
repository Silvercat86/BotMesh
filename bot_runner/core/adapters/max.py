import maxapi
from maxapi.enums.format import Format

class MaxAdapter:
    def __init__(self, bot):
        self.bot : maxapi.Bot = bot

    async def send(self, chat_id, text, photo=None):
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            attachments=[maxapi.types.InputMedia(photo)] if photo else None,
            parse_mode=Format.HTML,
        )