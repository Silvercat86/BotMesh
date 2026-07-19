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
from core.plugin_contracts import get_plugin_contracts, validate_plugin_config


log = logging.getLogger("bot.runner")


class BotRunner:
    def __init__(self, api_key: str, ping_interval: float = 10.0):
        self.api_key = api_key
        self.ping_interval = ping_interval

        self.session: aiohttp.ClientSession | None = None
        self.api: Api | None = None

        self._running = False

        self.bot_instances: dict[str, BotInstance] = {}
        self.bot_tasks: dict[str, asyncio.Task] = {}




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

        try:
            if self.api is None:
                raise RuntimeError("BotRunner API is not initialized")

            result = await self.api.validate_runner_contracts(get_plugin_contracts(PLUGIN_REGISTRY))
            if result.get("status") != "compatible":
                for error in result.get("errors", []):
                    log.error("Runner contract mismatch: %s", error)
                raise RuntimeError("Runner plugin contracts are incompatible with backend")

            self._running = True
            log.info("BotRunner started")

            while self._running:
                started_at = time.monotonic()

                try:
                    result = await self.api.get_active_bots()
                    active_bots = result.get("active_bots", [])

                    log.info("Backend ping ok. Active bots: %s", len(active_bots))

                    await self.actualize_bots(active_bots)

                except asyncio.CancelledError:
                    raise

                except Exception as e:
                    log.warning("Backend ping failed: %r", e)

                elapsed = time.monotonic() - started_at
                sleep_time = max(0.0, self.ping_interval - elapsed)

                await asyncio.sleep(sleep_time)

        finally:
            await self.shutdown()

    async def actualize_bots(self, active_bots: list[dict]) -> None:
        new_bots_by_name = {
            bot_data["name"]: bot_data
            for bot_data in active_bots
        }

        current_names = set(self.bot_instances.keys())
        new_names = set(new_bots_by_name.keys())

        for bot_name in current_names - new_names:
            log.info("Bot removed from backend, stopping: %s", bot_name)
            await self.stop_bot(bot_name)

        for bot_name in current_names & new_names:
            bot_instance = self.bot_instances[bot_name]
            bot_data = new_bots_by_name[bot_name]

            current_version = getattr(bot_instance, "version", None)
            new_version = bot_data.get("version")

            if current_version != new_version:
                log.info(
                    "Bot version changed, recreating: %s old=%r new=%r",
                    bot_name,
                    current_version,
                    new_version,
                )

                await self.stop_bot(bot_name)
                
                await asyncio.sleep(1) 

                await self.start_bot_from_data(bot_data)
        for bot_name in new_names - current_names:
            bot_data = new_bots_by_name[bot_name]

            log.info("New bot found, starting: %s", bot_name)
            
            await self.start_bot_from_data(bot_data)


    async def shutdown(self):
        self._running = False

        for bot_name in list(self.bot_instances.keys()):
            await self.stop_bot(bot_name)

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
                config = {key: value for key, value in plugin_data.items() if key != "name"}
                validate_plugin_config(plugin_class, config)
                plugin_instance = plugin_class.from_config(config)
                plugin_instance.name = plugin_data["name"]
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
                service_instance.name = service_data["name"]
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
        version = bot_data.get("version", 1)

        plugins = self.create_plugins_from_config(plugins_data)
        services = self.create_services_from_config(services_data)
        actions = self.create_actions_from_config(actions_data)

        if platform == "telegram":
            bot_instance = TelegramBotInstance(token, api_key, name, plugins, services, actions, version)
        elif platform == "max":
            bot_instance = MaxBotInstance(token, api_key, name, plugins, services, actions, version)
        else:
            log.warning("Unsupported platform: %s", platform)
            return None

        return bot_instance
    
    async def start_bot_from_data(self, bot_data: dict) -> None:
        bot_instance = await self.create_bot_instance(bot_data)

        if bot_instance is None:
            return

        await bot_instance.init_plugins()

        task = asyncio.create_task(bot_instance.run())

        self.bot_instances[bot_instance.name] = bot_instance
        self.bot_tasks[bot_instance.name] = task

        log.info(
            "Bot started: %s version=%r",
            bot_instance.name,
            getattr(bot_instance, "version", None),
        )

    async def stop_bot(self, bot_name: str) -> None:
        task = self.bot_tasks.pop(bot_name, None)
        bot_instance = self.bot_instances.pop(bot_name, None)

        if bot_instance is not None:
            await bot_instance.shutdown()

        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        

        log.info("Bot stopped: %s", bot_name)
    
    




            

        

