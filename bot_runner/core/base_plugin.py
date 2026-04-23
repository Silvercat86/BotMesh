from collections.abc import Callable

from aiogram import Router
import maxapi
from core.api import Api
from core.adapters.protocols import BotAdapter

class BasePlugin:
    required_services: tuple[str, ...] = ()

    def __init__(self):
        self.adapter: BotAdapter = None
        self.bot = None
        self.services = None
        self.api : Api = None
        self.bot_name = None
        self.router = Router()
        self.dp = None

    def get_actions(self) -> dict[str, Callable]:
        return {}
    
    def get_action(self, action_name: str) -> Callable:
        return self.get_actions().get(action_name)

    def setup(self):
        raise NotImplementedError()

    

