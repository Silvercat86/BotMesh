from aiogram import Router


class BasePlugin:
    required_services: tuple[str, ...] = ()

    def __init__(self):
        self.router = Router()
        self.bot = None
        self.services = None

    def setup(self):
        raise NotImplementedError()