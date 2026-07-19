# plugins/welcome/plugin.py

import logging
import random
import time
from typing import Callable, List, Dict, Tuple

from aiogram.types import ChatMemberUpdated, Message
from aiogram import F

from core.base_plugin import BasePlugin
from core.plugin_contracts import WelcomeConfig

DEFAULT_BASE_TEMPLATE = "Привет"
DEFAULT_QUESTIONS = ["Да?"]


class WelcomePlugin(BasePlugin):
    config_model = WelcomeConfig
    def __init__(
        self,
        base_template: str,
        questions: List[str],
        n_questions: int = 3,
        dedupe_ttl_seconds: int = 30,  # окно антидубля
    ):
        super().__init__()

        self.base_template = base_template
        self.questions = questions
        self.n_questions = n_questions
        self.dedupe_ttl_seconds = dedupe_ttl_seconds

        # (chat_id, user_id) -> expires_at_monotonic
        self._dedupe: Dict[Tuple[int, int], float] = {}


    @classmethod
    def from_config(cls, config):
        base_template = config.get("base_template",DEFAULT_BASE_TEMPLATE)
        questions = config.get("questions", DEFAULT_QUESTIONS)

        return cls(
            base_template,
            questions,
            n_questions=int(config.get("n_questions", 3)),
            dedupe_ttl_seconds=int(config.get("dedupe_ttl_seconds", 30)),
        )
        

    def get_actions(self) -> dict[str, Callable]:
        return {
            "handle_chat_member_join": self.handle_chat_member_join,
        }
    
    async def handle_chat_member_join(self, event):
        if hasattr(event, "new_chat_member"):
            # Telegram
            user = event.new_chat_member.user
            chat_id = event.chat.id
            user_id = user.id

        elif hasattr(event, "user"):
            # Max
            self.log.info(f"Received chat member event: {event}")

            user = event.user
            chat_id = event.chat_id
            user_id = user.user_id 

        else:
            return

        if getattr(user, "is_bot", False):
            return

        if not self._mark_once(chat_id, user_id):
            return

        await self._send_welcome(chat_id=chat_id, user=user)

    async def setup(self):
        self.log = logging.getLogger(f"[{self.bot_name}] birthdays")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )

    # ---------------- DEDUPE ----------------

    def _mark_once(self, chat_id: int, user_id: int) -> bool:
        """
        Возвращает True только первый раз в течение TTL.
        Второй триггер в течение TTL будет подавлен.
        """
        now = time.monotonic()
        self._cleanup(now)

        key = (chat_id, user_id)
        expires_at = self._dedupe.get(key)

        if expires_at and expires_at > now:
            return False

        self._dedupe[key] = now + self.dedupe_ttl_seconds
        return True

    def _cleanup(self, now: float) -> None:
        # простая очистка протухших ключей
        if not self._dedupe:
            return
        expired = [k for k, exp in self._dedupe.items() if exp <= now]
        for k in expired:
            self._dedupe.pop(k, None)

    # ---------------- SEND ----------------

    async def _send_welcome(self, chat_id: int, user):
        selected_questions = random.sample(
            self.questions,
            k=min(self.n_questions, len(self.questions)),
        )
        text = self._render_template(user, selected_questions)

        await self._send(
            chat_id=chat_id,
            text=text,
        )

    def _render_template(self, user, questions: List[str]) -> str:
        if user.username:
            mention = f" @{user.username}"
        else:
            mention = f" {user.first_name}"

        questions_block = "\n".join(f"- {q}" for q in questions)

        text = self.base_template
        text = text.replace("{mention}", mention)
        text = text.replace("{questions}", questions_block)
        return text
