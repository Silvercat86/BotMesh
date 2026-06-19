import asyncio
import logging
import time

import aiohttp

from core.api import Api

from core.bot_instance import BotInstance, TelegramBotInstance, MaxBotInstance
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
        self._shutting_down = False

        self.bot_instances: dict[str, BotInstance] = {}
        self.bot_tasks: dict[str, asyncio.Task] = {}
        self.bot_data_store: dict[str, dict] = {}
        self.bot_stop_events: dict[str, asyncio.Event] = {}
        self._actualize_lock = asyncio.Lock()

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

        self._running = True
        self._shutting_down = False
        log.info("BotRunner started")

        try:
            while self._running and not self._shutting_down:
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
        async with self._actualize_lock:
            new_bots_by_name = {
                bot_data["name"]: bot_data
                for bot_data in active_bots
            }

            current_names = set(self.bot_instances.keys())
            new_names = set(new_bots_by_name.keys())

            # Store bot data for restarts
            for bot_name, bot_data in new_bots_by_name.items():
                self.bot_data_store[bot_name] = bot_data

            # 1. Stop removed bots
            for bot_name in current_names - new_names:
                log.info("Bot removed from backend, stopping: %s", bot_name)
                await self.stop_bot(bot_name)
                if bot_name in self.bot_data_store:
                    del self.bot_data_store[bot_name]

            # 2. Restart changed bots
            for bot_name in current_names & new_names:
                bot_instance = self.bot_instances.get(bot_name)
                bot_data = new_bots_by_name[bot_name]

                if bot_instance is None:
                    continue

                current_version = str(getattr(bot_instance, "version", ""))
                new_version = str(bot_data.get("version", ""))

                if current_version != new_version:
                    log.info(
                        "Bot version changed, restarting: %s old=%s new=%s",
                        bot_name,
                        current_version,
                        new_version,
                    )

                    await self.restart_bot(bot_name, bot_data)

            # 3. Start new bots
            for bot_name in new_names - current_names:
                log.info("New bot found, starting: %s", bot_name)
                await self.start_bot_from_data(new_bots_by_name[bot_name])

    async def shutdown(self):
        self._shutting_down = True
        self._running = False

        log.info("Shutting down all bots...")
        
        # Stop all bots with proper cleanup
        for bot_name in list(self.bot_instances.keys()):
            await self.stop_bot(bot_name)

        # Close session
        if self.session is not None and not self.session.closed:
            await self.session.close()

        self.api = None
        self.session = None
        self.bot_data_store.clear()

        log.info("BotRunner stopped")

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
        bot_name = bot_data["name"]

        # Check if bot is already running
        if bot_name in self.bot_instances:
            bot_instance = self.bot_instances[bot_name]
            if bot_instance._is_running:
                log.warning("Bot already running, skip start: %s", bot_name)
                return

        # Check for existing task
        existing_task = self.bot_tasks.get(bot_name)
        if existing_task is not None and not existing_task.done():
            log.warning("Bot task still active, skip start: %s", bot_name)
            return

        # Clean up old references
        if bot_name in self.bot_instances:
            del self.bot_instances[bot_name]
        if bot_name in self.bot_tasks:
            del self.bot_tasks[bot_name]

        # Create bot instance
        bot_instance = await self.create_bot_instance(bot_data)

        if bot_instance is None:
            return

        # Initialize plugins
        await bot_instance.init_plugins()

        # Create task
        task = asyncio.create_task(bot_instance.run())

        # Store references
        self.bot_instances[bot_instance.name] = bot_instance
        self.bot_tasks[bot_instance.name] = task
        self.bot_data_store[bot_name] = bot_data

        log.info(
            "Bot started: %s version=%r platform=%s",
            bot_instance.name,
            getattr(bot_instance, "version", None),
            bot_data.get("platform", "unknown"),
        )

    async def stop_bot(self, bot_name: str) -> None:
        """Stop a bot instance with proper cleanup"""
        log.info("Stopping bot: %s", bot_name)
        
        # Get task and instance
        task = self.bot_tasks.pop(bot_name, None)
        bot_instance = self.bot_instances.pop(bot_name, None)

        # CRITICAL: Shutdown the bot instance FIRST
        if bot_instance is not None:
            log.info("Shutting down bot instance: %s", bot_name)
            try:
                # This will stop the polling and close connections
                await bot_instance.shutdown()
                log.info("Bot shutdown completed: %s", bot_name)
            except Exception as e:
                log.error("Error during bot shutdown: %s", e)
            
            # Wait for connections to fully close
            await asyncio.sleep(1.0)

        # Then cancel the task if it's still running
        if task is not None and not task.done():
            log.info("Cancelling bot task: %s", bot_name)
            task.cancel()
            
            # Wait for the task to actually complete
            try:
                await asyncio.gather(task, return_exceptions=True)
                log.info("Bot task cancelled successfully: %s", bot_name)
            except asyncio.CancelledError:
                log.info("Bot task cancellation confirmed: %s", bot_name)
            except Exception as e:
                log.warning("Error during task cancellation: %s", e)

        # Final cleanup
        self.bot_instances.pop(bot_name, None)
        self.bot_tasks.pop(bot_name, None)
        
        log.info("Bot fully stopped: %s", bot_name)

    async def restart_bot(self, bot_name: str, bot_data: dict) -> None:
        """Restart a bot with proper cleanup"""
        log.info("Restarting bot: %s", bot_name)
        
        # IMPORTANT: Stop the bot with full cleanup
        await self.stop_bot(bot_name)
        
        # CRITICAL: Wait for Telegram to release the session
        # This MUST be done before starting the new instance
        log.info("Waiting 3 seconds for Telegram session cleanup...")
        await asyncio.sleep(3.0)
        
        # Double-check that the bot is really stopped
        if bot_name in self.bot_instances:
            log.warning("Bot still in instances after stop, forcing cleanup...")
            self.bot_instances.pop(bot_name, None)
            
        if bot_name in self.bot_tasks:
            task = self.bot_tasks.pop(bot_name)
            if not task.done():
                task.cancel()
                try:
                    await asyncio.gather(task, return_exceptions=True)
                except:
                    pass
        
        # Start the bot again
        await self.start_bot_from_data(bot_data)
        
        log.info("Bot restarted: %s", bot_name)

    async def force_stop_bot(self, bot_name: str) -> None:
        """Force stop a bot (use only if normal stop fails)"""
        log.warning("Force stopping bot: %s", bot_name)
        
        # Get references
        task = self.bot_tasks.pop(bot_name, None)
        bot_instance = self.bot_instances.pop(bot_name, None)
        
        # Cancel task forcefully
        if task is not None:
            task.cancel()
            try:
                await asyncio.gather(task, return_exceptions=True)
            except:
                pass
        
        # Shutdown instance forcefully
        if bot_instance is not None:
            try:
                await bot_instance.shutdown()
            except:
                pass
        
        log.warning("Bot force stopped: %s", bot_name)

    async def stop_all_bots(self):
        """Stop all running bots"""
        log.info("Stopping all bots...")
        bot_names = list(self.bot_instances.keys())
        for bot_name in bot_names:
            await self.stop_bot(bot_name)
        log.info("All bots stopped")

    async def get_bot_status(self, bot_name: str) -> dict:
        """Get status of a bot"""
        bot_instance = self.bot_instances.get(bot_name)
        if bot_instance is None:
            return {"status": "not_found"}
        
        return {
            "name": bot_name,
            "is_running": bot_instance._is_running,
            "version": getattr(bot_instance, "version", None),
            "task_active": bot_name in self.bot_tasks and not self.bot_tasks[bot_name].done()
        }