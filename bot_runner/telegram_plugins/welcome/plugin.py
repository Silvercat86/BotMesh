# plugins/welcome/plugin.py

import random
import time
from typing import List, Dict, Tuple

from aiogram.types import ChatMemberUpdated, Message
from aiogram import F

from core.base_plugin import BasePlugin


class WelcomePlugin(BasePlugin):
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

    def setup(self):
        # 1) Service-message: new_chat_members (может работать без админки)
        @self.router.message(F.new_chat_members)
        async def greet_via_new_chat_members(message: Message):
            if not message.new_chat_members:
                return

            for user in message.new_chat_members:
                if user.is_bot:
                    continue
                if not self._mark_once(message.chat.id, user.id):
                    print(f"Suppressed welcome for {user.id} in chat {message.chat.id}")
                    continue
                await self._send_welcome(chat_id=message.chat.id, user=user)

        # 2) ChatMemberUpdated (часто требует админку, но более надёжно)
        @self.router.chat_member()
        async def greet_via_chat_member(event: ChatMemberUpdated):
            old = event.old_chat_member.status
            new = event.new_chat_member.status

            if old in ("left", "kicked") and new in ("member", "administrator"):
                user = event.new_chat_member.user
                if user.is_bot:
                    return
                if not self._mark_once(event.chat.id, user.id):
                    print(f"Suppressed welcome for {user.id} in chat {event.chat.id}")
                    return
                await self._send_welcome(chat_id=event.chat.id, user=user)

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

        await self.bot.send_message(
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