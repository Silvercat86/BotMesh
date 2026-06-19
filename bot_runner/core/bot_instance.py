# core/bot_instance.py
import aiogram
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import aiohttp
import logging
import asyncio

from core.services.container import ServiceContainer
from core.services import Services
from core.api import Api

from core.adapters.max import MaxAdapter
from core.adapters.telegram import TelegramAdapter
from core.base_plugin import BasePlugin

from aiogram.types import Message as TelegramMessage
from aiogram.filters import Command as TelegramCommand

from maxapi.types import Command as MaxCommand, MessageCreated as MaxMessageCreated

from core.action import Action, ActionType

import maxapi

log = logging.getLogger("bot.instance")


class BotInstance:
    def __init__(self, api_key: str, name: str, plugins: list, services: list, actions: list[Action] = None, version: int = 1):
        self.name = name
        self.actions = actions or []
        self.version = version
        self._is_running = False
        self._shutdown_complete = asyncio.Event()
        self._shutdown_complete.set()  # Initially complete

        self.http_session = aiohttp.ClientSession()
        self.api = Api(self.http_session, api_key)

        self.plugins: list[BasePlugin] = plugins

        container = ServiceContainer()

        for service in services:
            container.register(service.name, service)

        self.services = Services(container)

    async def _initialize_plugin(self, plugin: BasePlugin):
        if hasattr(plugin, "required_services"):
            self.services.ensure(plugin.required_services)

        plugin.adapter = self.adapter
        plugin.bot_name = self.name
        plugin.bot = self.bot
        plugin.services = self.services
        plugin.api = self.api

    async def shutdown(self):
        """Base shutdown method - to be overridden by subclasses"""
        self._is_running = False
        self._shutdown_complete.clear()
        await self.http_session.close()
        self._shutdown_complete.set()


class TelegramBotInstance(BotInstance):
    def __init__(self, token: str, api_key: str, name: str, plugins: list, services: list, actions: list[Action] = None, version: int = 1):
        super().__init__(api_key, name, plugins, services, actions, version)

        self.token = token
        self.dp = Dispatcher()
        self._polling_task = None
        self._stop_polling = False

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

        log.warning(f"Command '{action.name}' with function '{action.func_name}' not found in any plugin.")

    async def run(self):
        """Run the bot with proper cleanup"""
        if self._is_running:
            log.warning("Bot already running: %s", self.name)
            return

        self._is_running = True
        self._stop_polling = False
        self._shutdown_complete.clear()
        
        log.info("Starting polling for bot: %s", self.name)
        
        try:
            # Use the standard aiogram polling with error handling
            while not self._stop_polling:
                try:
                    # This will run until stopped or error
                    await self.dp.start_polling(
                        self.bot,
                        allowed_updates=self.dp.resolve_used_update_types()
                    )
                    break  # Normal exit
                except Exception as e:
                    if self._stop_polling:
                        break
                    log.error("Polling error: %s", e)
                    if not self._stop_polling:
                        log.info("Restarting polling after error...")
                        await asyncio.sleep(1)
                        continue
                    break
                    
        except asyncio.CancelledError:
            log.info("Polling cancelled for bot: %s", self.name)
        except Exception as e:
            log.error("Fatal error in bot %s: %s", self.name, e)
            raise
        finally:
            self._is_running = False
            self._shutdown_complete.set()
            log.info("Polling stopped for bot: %s", self.name)

    async def shutdown(self):
        """Proper shutdown for Telegram bot"""
        if self._shutdown_complete.is_set() and not self._is_running:
            log.info("Bot already shutdown: %s", self.name)
            return
            
        log.info("Shutting down Telegram bot: %s", self.name)
        
        # Signal stop
        self._stop_polling = True
        self._is_running = False
        
        # Stop polling gracefully
        if hasattr(self, 'dp') and self.dp is not None:
            try:
                log.info("Stopping polling for bot: %s", self.name)
                await self.dp.stop_polling()
                log.info("Polling stopped for bot: %s", self.name)
            except Exception as e:
                log.warning("Error stopping polling: %s", e)
        
        # Close bot session
        if hasattr(self, 'bot') and self.bot is not None:
            try:
                log.info("Closing bot session for: %s", self.name)
                await self.bot.session.close()
                log.info("Bot session closed for: %s", self.name)
            except Exception as e:
                log.warning("Error closing bot session: %s", e)
        
        # Close HTTP session
        await self.http_session.close()
        
        self._shutdown_complete.set()
        log.info("TelegramBotInstance shutdown complete for: %s", self.name)


class MaxBotInstance(BotInstance):
    def __init__(self, token: str, api_key: str, name: str, plugins: list, services: list, actions: list[Action] = None, version: int = 1):
        super().__init__(api_key, name, plugins, services, actions, version)

        self.token = token
        self.bot = maxapi.Bot(token)
        self.dp = maxapi.Dispatcher()
        self.adapter = MaxAdapter(self.bot)
        self._stop_polling = False

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

        log.warning(f"Action '{action.name}' not found")

    async def run(self):
        if self._is_running:
            log.warning("Bot already running: %s", self.name)
            return

        self._is_running = True
        self._stop_polling = False
        self._shutdown_complete.clear()
        
        log.info("Starting polling for Max bot: %s", self.name)
        
        try:
            await self.dp.start_polling(self.bot)
        except asyncio.CancelledError:
            log.info("Polling cancelled for Max bot: %s", self.name)
        except Exception as e:
            log.error("Error in polling for Max bot %s: %s", self.name, e)
            raise
        finally:
            self._is_running = False
            self._shutdown_complete.set()
            log.info("Polling stopped for Max bot: %s", self.name)

    async def shutdown(self):
        """Proper shutdown for Max bot"""
        if self._shutdown_complete.is_set() and not self._is_running:
            return
            
        log.info("Shutting down Max bot: %s", self.name)
        
        self._stop_polling = True
        self._is_running = False
        
        # Close HTTP session
        await self.http_session.close()
        
        self._shutdown_complete.set()
        log.info("MaxBotInstance shutdown complete for: %s", self.name)