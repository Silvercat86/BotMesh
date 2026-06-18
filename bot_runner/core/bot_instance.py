# core/bot_instance.py
import aiogram
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import aiohttp

from core.services.container import ServiceContainer
from core.services import Services
from core.api import Api

from core.adapters.max import MaxAdapter
from core.adapters.telegram import TelegramAdapter
from core.base_plugin import BasePlugin

from aiogram.types import Message as TelegramMessage
from aiogram.filters import Command as TelegramCommand

from maxapi.types import Command as MaxCommand,Message as MaxMessage,MessageCreated as MaxMessageCreated


from core.action import Action, ActionType



import maxapi
class BotInstance:
    def __init__(self, api_key: str, name: str, plugins: list, services: list, actions: list[Action] = None,version: int = 1):
        self.name = name
        self.actions = actions or []

        self.version = version

        self.http_session = aiohttp.ClientSession()
        self.api = Api(self.http_session, api_key)

        self.plugins : list[BasePlugin] = plugins


            

        container = ServiceContainer()

        for service in services:
            container.register(service.name, service)

        self.services = Services(container)

    

    async def _initialize_plugin(self, plugin : BasePlugin):
        if hasattr(plugin, "required_services"):
            self.services.ensure(plugin.required_services)

        plugin.adapter = self.adapter
        plugin.bot_name = self.name
        plugin.bot = self.bot
        plugin.services = self.services
        plugin.api = self.api

        


    

class TelegramBotInstance(BotInstance):
    def __init__(self, token: str,api_key:str, name: str, plugins: list, services: list, actions: list[Action] = None):

        super().__init__(api_key, name, plugins, services, actions)


        self.dp = Dispatcher()

        self.bot = aiogram.Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.adapter = TelegramAdapter(self.bot)



            



    async def init_plugins(self):
        for plugin in self.plugins:
            await super()._initialize_plugin(plugin)

            

            await plugin.setup()

            self.dp.include_router(plugin.router)
        self._register_actions()


    def _register_actions(self):


        for action in self.actions:
            self._register_telegram_action(action)

    def _register_telegram_action(self, action: Action):
        for plugin in self.plugins:
            plugin_action = plugin.get_action(action.func_name)
            if plugin_action:
                if action.type == ActionType.COMMAND:
                    async def wrapper(message: TelegramMessage):
                        universal_msg = self.adapter.convert_message(message)
                        return await plugin_action(universal_msg)
                    
                    self.dp.message.register(wrapper, TelegramCommand(action.name))
                    return
                if action.type == ActionType.CHAT_MEMBER_JOIN:
                    self.dp.chat_member.register(plugin_action, lambda e: e.new_chat_member.status == "member")
                    return
                if action.type == ActionType.CHAT_MEMBER_LEAVE:
                    self.dp.chat_member.register(plugin_action, lambda e: e.left_chat_member is not None)
                    return

        print(f"Warning: Command '{action.name}' with function '{action.func_name}' not found in any plugin.")
            
        

            

    async def run(self):
        await self.dp.start_polling(self.bot)

    async def shutdown(self):
        await self.http_session.close()
        await self.bot.session.close()


class MaxBotInstance(BotInstance):
    def __init__(self, token: str, api_key: str, name: str, plugins: list, services: list, actions: list[Action] = None):
        super().__init__(api_key, name, plugins, services, actions)

        self.bot = maxapi.Bot(token)
        self.dp = maxapi.Dispatcher()
        self.adapter = MaxAdapter(self.bot)
        

        

    async def init_plugins(self):
        
        for plugin in self.plugins:

            await super()._initialize_plugin(plugin)

           
            plugin.dp = self.dp
        
            await plugin.setup()

        self._register_actions()

    def _register_actions(self):
        for action in self.actions:
            self._register_max_action(action)

    def _register_max_action(self, action: Action):
        for plugin in self.plugins:
            plugin_action = plugin.get_action(action.func_name)

            if not plugin_action:
                continue

            if action.type == ActionType.COMMAND:
                async def wrapper(event: MaxMessageCreated):
                    universal_msg = self.adapter.convert_message(event)
                    return await plugin_action(universal_msg)
                
                self.dp.message_created.register(wrapper, MaxCommand(action.name))
                return

            if action.type == ActionType.CHAT_MEMBER_JOIN:
                self.dp.user_added.register(plugin_action)
                return

            if action.type == ActionType.CHAT_MEMBER_LEAVE:
                self.dp.user_removed.register(plugin_action)
                return

        print(f"Warning: Action '{action.name}' not found")

    async def run(self):
        await self.dp.start_polling(self.bot)

    async def shutdown(self):
        await self.http_session.close()