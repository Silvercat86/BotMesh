import logging

from core.base_plugin import BasePlugin
from core.plugin_contracts import StartConfig
import random
from typing import Callable, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command,CommandStart
from core.models import UniversalMessage

DEFAULT_TEMPLATES = ["Привет! Я бот сопровождения. По вопросам можешь обратиться @KatyaLay7"]
    
class StartPlugin(BasePlugin):
    config_model = StartConfig
    def __init__(self,messages: List[str]):
        super().__init__()
        self.messages = messages

    @classmethod
    def from_config(cls, config):
        messages = config.get("messages",DEFAULT_TEMPLATES)
        return cls(messages)

    async def start(self,message:UniversalMessage):
        chat_id = message.chat_id

        text = random.choice(self.messages)

        await self._send(chat_id=chat_id,text=text)

    def get_actions(self) -> dict[str, Callable]:
        return {
            "start": self.start,
        }

    async def setup(self):
        
        self.log = logging.getLogger(f"[{self.bot_name}] work_experience")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

