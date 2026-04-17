from aiogram import Bot
from aiogram.types import FSInputFile


class TelegramAdapter:
    def __init__(self, bot):
        self.bot = bot

    async def send(self, chat_id, text, photo=None):
        if photo:
            file = FSInputFile(photo)
            await self.bot.send_photo(chat_id, photo=file, caption=text)
        else:
            await self.bot.send_message(chat_id, text)