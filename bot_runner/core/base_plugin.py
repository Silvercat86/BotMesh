from aiogram import Router
import maxapi
from core.api import Api
from core.adapters.protocols import BotAdapter




class BaseTelegramPlugin:
    required_services: tuple[str, ...] = ()

    def __init__(self):
        self.adapter: BotAdapter = None
        self.router = Router()
        self.bot = None
        self.services = None
        self.api : Api = None

    def setup(self):
        raise NotImplementedError()
    

class BaseMaxPlugin:
    def __init__(self):
        self.bot : maxapi.Bot = None
        self.dp = None
        self.services = None
        self.api = None
        self.bot_name = None

    def setup(self):
        raise NotImplementedError