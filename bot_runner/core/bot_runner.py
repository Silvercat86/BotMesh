import asyncio
import logging
import time

import aiohttp

from core.api import Api

from core.bot_instance import BotInstance, TelegramBotInstance,MaxBotInstance
from core.registries import PLUGIN_REGISTRY, SERVICE_REGISTRY

from core.base_service import BaseService
from core.base_plugin import BasePlugin
from core.action import Action, get_action_type_from_string


log = logging.getLogger("bot.runner")


class BotRunner:
    def __init__(self, api_key: str, ping_interval: float = 10.0):
        self.api_key = api_key
        self.ping_interval = ping_interval

        self.session: aiohttp.ClientSession | None = None
        self.api: Api | None = None

        self._running = False
        self.a = False

        self.bot_instances: dict[str, BotInstance] = {}
        self.bot_tasks: list[asyncio.Task] = []




    async def init(self):
        if self.session is not None and not self.session.closed:
            return

        self.session = aiohttp.ClientSession()
        self.api = Api(
            session=self.session,
            api_key=self.api_key,
        )

    async def run(self):
        await self.init()

        if self.api is None:
            raise RuntimeError("BotRunner API is not initialized")

        log.info("BotRunner started")

        try:
            result = await self.api.get_active_bots()
            active_bots = result.get("active_bots", [])

            await self.create_bot_instances(active_bots)
            await self.init_bot_plugins()
            self.start_bot_tasks()

            if self.bot_tasks:
                await asyncio.gather(*self.bot_tasks)

        except asyncio.CancelledError:
            raise

        finally:
            await self.shutdown()

    async def shutdown(self):
        for task in self.bot_tasks:
            task.cancel()

        if self.bot_tasks:
            await asyncio.gather(*self.bot_tasks, return_exceptions=True)

        for bot_instance in self.bot_instances.values():
            await bot_instance.shutdown()

        if self.session is not None and not self.session.closed:
            await self.session.close()

        self.api = None
        self.session = None

        log.info("BotRunner stopped")

    def start_bot_tasks(self):
        for bot_instance in self.bot_instances.values():
            task = asyncio.create_task(bot_instance.run())
            self.bot_tasks.append(task)

            log.info("Bot task started: %s", bot_instance.name)

    async def init_bot_plugins(self):
        for bot_instance in self.bot_instances.values():
            await bot_instance.init_plugins()
            log.info("Plugins initialized for bot: %s", bot_instance.name)

    async def create_bot_instances(self, bot_data_list):
        
        try:
            for bot_data in bot_data_list:
                bot_instance = await self.create_bot_instance(bot_data)
                if bot_instance is None:
                    continue

                self.bot_instances[bot_instance.name] = bot_instance

                log.info("Bot instance created: %s", bot_instance.name)
        except Exception as e:
            log.error("Error initializing bot instances: %r", e)
            

            
    def create_plugins_from_config(self, plugins_data: list[dict]) -> list[BasePlugin]:
        plugin_instances = []
        for plugin_data in plugins_data:

            plugin_class = PLUGIN_REGISTRY.get(plugin_data["name"])
            if plugin_class is None:
                log.warning("Plugin %s not found in registry", plugin_data["name"])
                continue
            else:
                plugin_instance = plugin_class.from_config(plugin_data)
                plugin_instances.append(plugin_instance)

        return plugin_instances
    
    def create_services_from_config(self, services_data: list[dict]) -> list[BaseService]:
        service_instances = []
        for service_data in services_data:
            service_class = SERVICE_REGISTRY.get(service_data["name"])
            if service_class is None:
                log.warning("Service %s not found in registry", service_data["name"])
                continue
            else:
                service_instance = service_class.from_config(service_data)
                service_instances.append(service_instance)

        return service_instances
    
    def create_actions_from_config(self, actions_data: list[dict]) -> list[Action]:
        action_instances = []
        for action_data in actions_data:
            action_name = action_data.get("name")
            action_func_name = action_data.get("func_name")
            action_type = action_data.get("type")
            action_scope = action_data.get("scope")
            action = Action(
                name=action_name,
                func_name=action_func_name,
                type=get_action_type_from_string(action_type),
                scope=action_scope
            )
            log.info("Action created: %s", action_name)
            action_instances.append(action)

        return action_instances
    
    async def create_bot_instance(self, bot_data: dict) -> BotInstance | None:
        token = bot_data["token"]
        api_key = bot_data["api_key"]
        name = bot_data["name"]
        platform = bot_data["platform"]
        plugins_data = bot_data["plugins"]
        services_data = bot_data["services"]
        actions_data = bot_data["actions"]

        plugins = self.create_plugins_from_config(plugins_data)
        services = self.create_services_from_config(services_data)
        actions = self.create_actions_from_config(actions_data)

        if platform == "telegram":
            bot_instance = TelegramBotInstance(token, api_key, name, plugins, services, actions)
        elif platform == "max":
            bot_instance = MaxBotInstance(token, api_key, name, plugins, services, actions)
        else:
            log.warning("Unsupported platform: %s", platform)
            return None

        return bot_instance
    
    




            

        

