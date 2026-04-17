import maxapi


class MaxAdapter:
    def __init__(self, bot):
        self.bot = bot

    async def send(self, chat_id, text, photo=None):
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            attachments=[maxapi.types.InputMedia(photo)] if photo else None
        )