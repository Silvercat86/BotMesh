import unittest
from unittest.mock import AsyncMock, patch

from core.bot_runner import BotRunner


class BotRunnerCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_incompatible_contract_prevents_start_and_closes_resources(self):
        runner = BotRunner(api_key="runner-key")
        api = AsyncMock()
        api.validate_runner_contracts.return_value = {
            "status": "incompatible",
            "errors": [{"type": "missing_plugin", "plugin": "test"}],
        }

        async def fake_init():
            runner.api = api

        runner.init = fake_init
        runner.shutdown = AsyncMock()

        with patch("core.bot_runner.get_plugin_contracts", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "incompatible"):
                await runner.run()

        runner.shutdown.assert_awaited_once()
        api.get_active_bots.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
