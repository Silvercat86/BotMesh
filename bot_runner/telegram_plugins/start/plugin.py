from core.base_plugin import BaseTelegramPlugin
import random
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command,CommandStart

class StartPlugin(BaseTelegramPlugin):
    def __init__(self,messages: List[str]):
        super().__init__()
        self.messages = messages



    def setup(self):
        @self.router.message(CommandStart())
        async def start_command(message: Message):
            print(f"Received /start command from {message.from_user.id}")
            if self.messages:
                await message.reply(random.choice(self.messages))
            else:
                await message.reply("Привет! Я бот сопровождения. По вопросам можешь обратиться @KatyaLay7")
