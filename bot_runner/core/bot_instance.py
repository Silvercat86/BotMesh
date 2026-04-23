# core/bot_instance.py
import aiogram
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import aiohttp

from core.services.container import ServiceContainer
from core.services import Services
from core.api import Api

from core.adapters.max import MaxAdapter
from core.adapters.telegram import TelegramAdapter
from core.base_plugin import BasePlugin

from aiogram.types import Message
from aiogram.filters import Command as AiogramCommand

from core.command import Command

import maxapi
class BotInstance:
    def __init__(self, api_key: str, name: str, plugins: list, services: list, commands: list[Command] = None):
        self.name = name
        self.commands = commands or []

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

        if hasattr(plugin, "register_commands"):
            await plugin.register_commands()


    

class TelegramBotInstance(BotInstance):
    def __init__(self, token: str,api_key:str, name: str, plugins: list, services: list, commands: list[Command] = None):

        super().__init__(api_key, name, plugins, services, commands)


        self.dp = Dispatcher()

        self.bot = aiogram.Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.adapter = TelegramAdapter(self.bot)



            



    async def init_plugins(self):
        for plugin in self.plugins:
            await super()._initialize_plugin(plugin)

            

            plugin.setup()

            self.dp.include_router(plugin.router)
        self._register_commands()


    def _register_commands(self):


        for cmd in self.commands:
            self._register_telegram_command(cmd)

    def _register_telegram_command(self, cmd: Command):
        for plugin in self.plugins:
            action = plugin.get_action(cmd.func_name)
            if action:
                self.dp.message.register(action, AiogramCommand(cmd.name))
                return
        print(f"Warning: Command '{cmd.name}' with function '{cmd.func_name}' not found in any plugin.")
            
        

            

    async def run(self):
        await self.dp.start_polling(self.bot)

    async def shutdown(self):
        await self.http_session.close()
        await self.bot.session.close()


class MaxBotInstance(BotInstance):
    def __init__(self, token: str, api_key: str, name: str, plugins: list, services: list, commands: list[Command] = None):
        super().__init__(api_key, name, plugins, services, commands)

        self.bot = maxapi.Bot(token)
        self.dp = maxapi.Dispatcher()
        self.adapter = MaxAdapter(self.bot)
        

        

    async def init_plugins(self):
        
        for plugin in self.plugins:

            await super()._initialize_plugin(plugin)

           
            plugin.dp = self.dp
        
            plugin.setup()

    async def run(self):
        await self.dp.start_polling(self.bot)

    async def shutdown(self):
        await self.http_session.close()