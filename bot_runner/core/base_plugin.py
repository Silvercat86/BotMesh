from aiogram import Router
import maxapi
from core.api import Api


class BaseTelegramPlugin:
    required_services: tuple[str, ...] = ()

    def __init__(self):
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