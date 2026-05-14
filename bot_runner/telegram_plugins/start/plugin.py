import logging

from core.base_plugin import BasePlugin
import random
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command,CommandStart
from core.models import UniversalMessage
    
class StartPlugin(BasePlugin):
    def __init__(self,messages: List[str]):
        super().__init__()
        self.messages = messages

    async def start(self,message:UniversalMessage):
        chat_id = message.chat_id

        text = random.choice(self.messages)

        await self._send(chat_id=chat_id,text=text)

    async def setup(self):
        
        self.log = logging.getLogger(f"[{self.bot_name}] work_experience")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        


        @self.router.message(CommandStart())
        async def start_command(message: Message):
            print(f"Received /start command from {message.from_user.id}")
            if self.messages:
                await message.reply(random.choice(self.messages))
            else:
                await message.reply("Привет! Я бот сопровождения. По вопросам можешь обратиться @KatyaLay7")
