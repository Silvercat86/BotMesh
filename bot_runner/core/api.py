import aiohttp
import asyncio
import logging
import random
import uuid
from typing import Any, Optional
from core.utils.serializers import build_user_payload
import os
from aiogram.types import Message

log = logging.getLogger("bot.api")

API_BASE_URL = os.getenv("BACKEND_API_URL","http://bot-platform:8000/api/") 
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=8)

RETRIES = 2
MAX_BACKOFF = 5

class APIClientError(Exception):
    pass

class APIServerError(Exception):
    pass

class APINetworkError(Exception):
    pass

class Api:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.api_url = API_BASE_URL
        self.api_key = os.getenv("BOT_API_KEY")
        if not self.api_key:
            log.error("No api key provided")
        

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        url = API_BASE_URL + path
        last_error = None

        request_id = str(uuid.uuid4())

        headers = {
            "X-Request-ID": request_id,
            "X-API-KEY": self.api_key,
        }

        for attempt in range(RETRIES + 1):
            try:
                async with self.session.request(
                    method,
                    url,
                    json = json,
                    timeout=DEFAULT_TIMEOUT,
                    headers=headers,
                ) as resp:

                    text = await resp.text()

                    try:
                        data = await resp.json()
                    except Exception:
                        data = {"raw": text}

                    if 500 <= resp.status < 600:
                        raise APIServerError(data)

                    if 400 <= resp.status < 500:
                        log.warning(
                            "API client error %s %s [%s] req_id=%s: %s",
                            method,
                            url,
                            resp.status,
                            request_id,
                            data,
                        )
                        raise APIClientError(data)

                    return data

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e

                log.warning(
                    "API request failed (%s/%s) %s %s req_id=%s: %s",
                    attempt + 1,
                    RETRIES + 1,
                    method,
                    url,
                    request_id,
                    repr(e),
                )

                if attempt >= RETRIES:
                    break

                delay = min(2 ** attempt, MAX_BACKOFF) + random.uniform(0, 0.3)
                await asyncio.sleep(delay)

        log.error(
            "API unreachable %s %s req_id=%s: %s",
            method,
            url,
            request_id,
            repr(last_error),
        )

        raise APINetworkError(data)

    async def get_context(self, message: Message):
        payload = {
            "user":  message.from_user.id,
            "chat":  message.chat.id,
        }

        log.info("SENDING JSON: %s", payload)

        return await self._request("POST", "context/", json=payload)

    