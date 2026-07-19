import aiohttp
import asyncio
import logging
import random
import uuid
from typing import Any, Optional
import os
from aiogram.types import Message,User,Chat

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
    def __init__(self, session: aiohttp.ClientSession,api_key:str):
        self.session = session
        self.api_url = API_BASE_URL
        self.api_key = api_key
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
        url = self.api_url + path
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
                    params=params
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

        raise APINetworkError(str(last_error))

    async def get_context(self, message: Message) -> dict[str, Any]:
        payload = {
            "user": build_user_payload(message.from_user),
            "chat": build_chat_payload(message.chat)
        }

        return await self._request("POST", "context/", json=payload)
    
    async def save_plugin_state(self, plugin_name: str,state: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "plugin": plugin_name,
            "state": state
        }
        return await self._request("POST", "save_plugin_state/", json=payload)
    
    async def load_plugin_state(self, plugin_name: str) -> dict[str, Any]:
        params = {"plugin": plugin_name}
        return await self._request("GET", "load_plugin_state/", params=params)
    
    async def get_active_bots(self):
        return await self._request("GET", "active_bots/")

    async def validate_runner_contracts(self, plugins: dict[str, dict]) -> dict[str, Any]:
        return await self._request(
            "POST",
            "runner/validate_contracts/",
            json={"plugins": plugins},
        )
    
    async def get_template_pack(self,plugin_name,template_name) -> dict[str, Any]:
        params = {
            "template" : template_name,
            "plugin" : plugin_name
        }
        log.info(f"asking for template {template_name} {plugin_name}")
        return await self._request("GET","get_template_pack/",params=params)
    
    
    
    


    

def build_user_payload(user:User):
    payload = {
        "id" : user.id,
        "username" : user.username,
        "first_name" : user.first_name,
        "last_name" : user.last_name
    }
    return payload

def build_chat_payload(chat:Chat):
    payload = {
        "id" : chat.id,
        "type" : chat.type,
        "title" : chat.username if chat.type == "private" else chat.title
        
    }
    return payload

