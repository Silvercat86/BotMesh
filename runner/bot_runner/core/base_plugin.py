import asyncio
import logging
from typing import Any, Callable
from typing import  Self

from aiogram import Router
from core.api import Api
from core.adapters.protocols import BotAdapter

class BasePlugin:
    config_model = None
    required_services: tuple[str, ...] = ()
    action_contracts: dict[str, dict] = {}

    def __init__(self):
        self.adapter: BotAdapter = None
        self.bot = None
        self.services = None
        self.api : Api = None
        self.name : str = None
        self.default_state = {}
        self.bot_name = None
        self.router = Router()
        self.dp = None
        self._background_tasks: set[asyncio.Task] = set()

    def start_background_task(self, coroutine):
        task = asyncio.create_task(coroutine)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_task_finished)
        return task

    def _background_task_finished(self, task):
        self._background_tasks.discard(task)
        if not task.cancelled() and (error := task.exception()) is not None:
            logging.getLogger("bot.plugin").error(
                "Background task failed for plugin %s on bot %s: %r",
                self.name, self.bot_name, error,
            )

    async def shutdown(self):
        tasks = list(self._background_tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        

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
    
    @classmethod
    def from_config(cls, config: dict) -> Self:
        return cls()
        
    
    async def get_template_pack(self,template_name)  -> dict[str, Any]:
        response = await self.api.get_template_pack(plugin_name=self.name,template_name=template_name)
        template_pack = response.get("template_pack")


        return template_pack

    async def setup(self):
        raise NotImplementedError()

    

