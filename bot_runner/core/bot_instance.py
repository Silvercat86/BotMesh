# core/bot_instance.py
import aiogram
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import aiohttp

from core.services.container import ServiceContainer
from core.services import Services
from core.api import Api


class TelegramBotInstance:
    def __init__(self, token: str,api_key:str, name: str, plugins: list, services: list):
        self.dp = Dispatcher()
        self.name = name

        self.bot = aiogram.Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.http_session = aiohttp.ClientSession()
        self.api = Api(self.http_session,api_key)

        self.plugins = plugins

        for plugin in plugins:
            plugin.api = self.api


        container = ServiceContainer()

        for service in services:
            container.register(service.name, service)

            

        self.services = Services(container)


    async def init_plugins(self):
        for plugin in self.plugins:
            

            if hasattr(plugin, "required_services"):
                self.services._c.ensure(plugin.required_services)

            plugin.bot_name = self.name
            plugin.bot = self.bot
            plugin.services = self.services

            if hasattr(plugin,"register_commands"):
                await plugin.register_commands()

            plugin.setup()

            self.dp.include_router(plugin.router)

    async def run(self):
        await self.dp.start_polling(self.bot)

    async def shutdown(self):
        await self.http_session.close()
        await self.bot.session.close()


class MaxBotInstance:
    def __init__(self, token: str,api_key:str, name: str, plugins: list, services: list):
        pass

    async def init_plugins(self):
        pass
    async def run(self):
        pass
    async def shutdown(self):
        pass