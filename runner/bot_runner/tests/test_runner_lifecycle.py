import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from core.base_plugin import BasePlugin
from core.bot_instance import MaxBotInstance, TelegramBotInstance
from core.bot_runner import BotRunner
from plugins.march8.plugin import March8Plugin


def bot_data(name, version=1):
    return {"name": name, "version": version, "plugins": [], "services": []}


class FakeBot:
    def __init__(self, name, version, *, fail=False):
        self.name = name
        self.version = version
        self.fail = fail
        self.initialized = False
        self.closed = False
        self.polling = False

    async def init_plugins(self):
        self.initialized = True
        if self.fail:
            raise RuntimeError("setup failed")

    async def run(self):
        self.polling = True
        try:
            await asyncio.Future()
        finally:
            self.polling = False

    async def shutdown(self):
        if self.polling:
            raise AssertionError("polling was still active during shutdown")
        self.closed = True


class RunnerLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_completed_polling_is_restarted_without_version_change(self):
        runner = BotRunner("key")
        first = FakeBot("one", 1)
        second = FakeBot("one", 1)
        instances = iter((first, second))
        runner.create_bot_instance = AsyncMock(side_effect=lambda data: next(instances))

        await runner.actualize_bots([bot_data("one")])
        await asyncio.sleep(0)
        runner.bot_tasks["one"].cancel()
        await asyncio.gather(runner.bot_tasks["one"], return_exceptions=True)
        await runner.actualize_bots([bot_data("one")])
        self.assertNotIn("one", runner.bot_instances)
        runner.retry_after["one"] = 0
        await runner.actualize_bots([bot_data("one")])

        self.assertTrue(first.closed)
        self.assertIs(runner.bot_instances["one"], second)
        await runner.shutdown()
        self.assertTrue(second.closed)
        self.assertFalse(second.polling)

    async def test_failed_setup_is_cleaned_and_does_not_block_other_bots(self):
        runner = BotRunner("key")
        broken = FakeBot("broken", 1, fail=True)
        healthy = FakeBot("healthy", 1)
        runner.create_bot_instance = AsyncMock(
            side_effect=lambda data: broken if data["name"] == "broken" else healthy
        )

        await runner.actualize_bots([bot_data("broken"), bot_data("healthy")])

        self.assertTrue(broken.closed)
        self.assertIn("healthy", runner.bot_instances)
        self.assertIn("broken", runner.retry_after)
        await runner.shutdown()

    async def test_stopped_schedule_restarts_bot_even_while_polling_runs(self):
        runner = BotRunner("key")
        first = FakeBot("one", 1)
        second = FakeBot("one", 1)
        instances = iter((first, second))
        runner.create_bot_instance = AsyncMock(side_effect=lambda data: next(instances))
        await runner.actualize_bots([bot_data("one")])
        await asyncio.sleep(0)
        schedule_task = asyncio.create_task(asyncio.sleep(0))
        await schedule_task
        first.plugins = [SimpleNamespace(_schedule_task=schedule_task)]

        await runner.actualize_bots([bot_data("one")])
        self.assertTrue(first.closed)
        runner.retry_after["one"] = 0
        await runner.actualize_bots([bot_data("one")])

        self.assertIs(runner.bot_instances["one"], second)
        await runner.shutdown()

    async def test_invalid_update_keeps_old_bot_running(self):
        runner = BotRunner("key")
        old = FakeBot("one", 1)
        runner.create_bot_instance = AsyncMock(return_value=old)
        await runner.actualize_bots([bot_data("one")])
        await asyncio.sleep(0)

        invalid = bot_data("one", 2)
        invalid["plugins"] = [{"name": "missing_plugin"}]
        await runner.actualize_bots([invalid])

        self.assertIs(runner.bot_instances["one"], old)
        self.assertFalse(old.closed)
        self.assertTrue(old.polling)
        await runner.shutdown()

    async def test_background_tasks_stop_with_plugin(self):
        plugin = BasePlugin()
        task = plugin.start_background_task(asyncio.sleep(3600))
        await asyncio.sleep(0)

        await plugin.shutdown()

        self.assertTrue(task.done())
        self.assertTrue(task.cancelled())

    async def test_schedules_are_isolated_per_plugin_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            first = March8Plugin("first", directory, hour=6, chat_id=1)
            second = March8Plugin("second", directory, hour=7, chat_id=2)
            first._register_daily_job()
            second._register_daily_job()

            self.assertEqual(len(first.scheduler.jobs), 1)
            self.assertEqual(len(second.scheduler.jobs), 1)
            self.assertIsNot(first.scheduler, second.scheduler)
            first.scheduler.clear()
            self.assertEqual(len(second.scheduler.jobs), 1)

    async def test_unstarted_adapters_close_their_sessions(self):
        telegram = TelegramBotInstance(
            "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi", "key", "telegram", [], []
        )
        maximum = MaxBotInstance("test-token", "key", "max", [], [])

        await telegram.shutdown()
        await maximum.shutdown()

        self.assertTrue(telegram.http_session.closed)
        self.assertTrue(maximum.http_session.closed)


if __name__ == "__main__":
    unittest.main()
