from core.base_plugin import BaseTelegramPlugin
from aiogram.filters import Command
from aiogram.types import Message
import os
import httpx
import logging

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")




class CleverShmaPlugin(BaseTelegramPlugin):
    def __init__(self):
        super().__init__()

        self.log = None

    def setup(self):

        self.log = logging.getLogger(f"[{self.bot_name}] schma")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )

        @self.router.message()
        async def test_handler(message: Message):
            bot_username = (await self.bot.get_me()).username

            is_mentioned = message.text and f"@{bot_username}" in message.text
            is_reply_to_bot = (
                message.reply_to_message
                and message.reply_to_message.from_user
                and message.reply_to_message.from_user.id == self.bot.id
            )

            if not (is_mentioned or is_reply_to_bot):
                return

            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://llm-gateway",
                "X-Title": "OutlinesHR-Gateway",
            }

            self.log.info(f"Triggered by message: {message.text}")

            # чистим упоминание чтобы не слать его в модель
            text = message.text.replace(f"@{bot_username}", "").strip() if message.text else ""

            question = f"""
Ты — максимально токсичный, туповатый, но смешной ассистент.

Твой стиль:
- постоянно шутишь, даже если вопрос серьезный
- используешь мат (умеренно, но регулярно)
- любишь тупые и абсурдные шутки
- можешь подкалывать собеседника
- допускаются грубые подколы и "шутки за 300"
- ведешь себя как друг, который постоянно рофлит и не воспринимает ничего всерьез

Важно:
- не будь злым ради злости, ты не агрессор, а клоун-токсик
- шутки могут быть тупыми, странными или кринжовыми — это нормально
- иногда можешь отвечать максимально нелепо
- не используй HTML

Отвечай коротко, дерзко и с юмором.

Вопрос:
{message.text}
"""

            payload = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": question,
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            }

            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(
                        OPENROUTER_URL,
                        json=payload,
                        headers=headers,
                    )

                data = r.json()
                self.log.info(data)

                answer = data.get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа")

                await message.reply(answer)

            except Exception as e:
                self.log.error(f"Error in CleverShmaPlugin: {e}")

