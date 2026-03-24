from aiogram import Router
from core.api import Api


class BasePlugin:
    required_services: tuple[str, ...] = ()

    def __init__(self):
        self.router = Router()
        self.bot = None
        self.services = None
        self.api : Api = None

    def setup(self):
        raise NotImplementedError()