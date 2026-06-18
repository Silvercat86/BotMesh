import asyncio
import logging
import time

import aiohttp

from core.api import Api


log = logging.getLogger("bot.runner")


class BotRunner:
    def __init__(self, api_key: str, ping_interval: float = 10.0):
        self.api_key = api_key
        self.ping_interval = ping_interval

        self.session: aiohttp.ClientSession | None = None
        self.api: Api | None = None

        self._running = False

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
        log.info("BotRunner started")

        while self._running:
            started_at = time.monotonic()

            try:
                result = await self.api.get_active_bots()
                log.info("Backend ping ok: %s", result)

            except asyncio.CancelledError:
                raise

            except Exception as e:
                log.warning("Backend ping failed: %r", e)

            elapsed = time.monotonic() - started_at
            sleep_time = max(0.0, self.ping_interval - elapsed)

            await asyncio.sleep(sleep_time)

    async def shutdown(self):
        self._running = False

        if self.session is not None and not self.session.closed:
            await self.session.close()

        self.api = None
        self.session = None

        log.info("BotRunner stopped")