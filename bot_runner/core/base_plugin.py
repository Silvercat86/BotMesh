import asyncio
from typing import Callable

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
        self.name : str = self.__class__.__name__
        self.default_state = {}
        self.bot_name = None
        self.router = Router()
        self.dp = None

    async def _send(self, chat_id: str, text: str, photo: str | None = None):
        await self.adapter.send(chat_id, text, photo)

    async def _load_state(self) -> dict:
        response = await self.api.load_plugin_state(self.name)
        self.log.info(f"load_plugin_state response: {self.name}")
        if response.get("status") == "success":
            state = response.get("state")
            if not state:
                state = self.default_state.copy()
                await self._save_state(state)
            return state
        else:
            self.log.error(f"Failed to load state for plugin {self.name} loading default state: {self.default_state.copy()}")
            return self.default_state.copy()
    async def _save_state(self, state: dict):
        response = await self.api.save_plugin_state(self.name, state)
        self.log.info(f"save_plugin_state response: {self.name}")
        if response.get("status") != "success":
            self.log.error(f"Failed to save state for plugin {self.name}: {response}")
        return response
    
    def get_actions(self) -> dict[str, Callable]:
        return {}
    
    def get_action(self, action_name: str) -> Callable:
        return self.get_actions().get(action_name)

    async def setup(self):
        raise NotImplementedError()

    

