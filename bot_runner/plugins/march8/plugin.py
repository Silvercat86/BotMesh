import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import schedule
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from core.base_plugin import BasePlugin


class March8Plugin(BasePlugin):
    def __init__(
        self,
        template: str,
        storage_dir: str,
        photo: str | None = None,
        hour: int = 9,
        minute: int = 0,
        chat_id: int | None = None,
        chat_file: str | None = None,
    ):
        super().__init__()

        self.template = template
        self.photo = photo

        self.hour = hour
        self.minute = minute

        self.chat_id = chat_id
        self.chat_file = Path(chat_file) if chat_file else None

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.state_path = self.storage_dir / "march8_state.json"

        self._schedule_task = None
        self.log = None

    # -------------------- SETUP --------------------

    async def setup(self):

        self.log = logging.getLogger(f"[{self.bot_name}] march8")

        if self.chat_file:
            self.chat_id = self._load_chat_id_from_file()

        path = Path(self.photo)

        if not path.exists():
            self.log.error(f"Photo not found: {path}")

        @self.router.message(Command("march8_test"))
        async def march8_test(message: Message):

            if not self.chat_id:
                await message.reply("❌ chat_id не задан")
                return

            await self._send()

        self._schedule_task = asyncio.create_task(self._schedule_loop())

    # -------------------- CHAT LOAD --------------------

    def _load_chat_id_from_file(self) -> int | None:

        if not self.chat_file or not self.chat_file.exists():
            self.log.warning("March8Plugin: chat file not found, no chat_id loaded")
            return None

        with open(self.chat_file, "r", encoding="utf-8") as f:
            line = f.readline().strip()

            try:
                chat_id = int(line)
                self.log.info(f"March8Plugin: loaded chat_id {chat_id} from file")
                return chat_id
            except ValueError:
                self.log.error(f"March8Plugin: invalid chat_id in file: {line}")
                return None

    # -------------------- STATE --------------------

    def _load_state(self):

        if not self.state_path.exists():
            return {}

        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_state(self, state):

        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    # -------------------- SEND --------------------

    async def _send(self):

        try:

            if self.photo:

                path = Path(self.photo)

                if not path.exists():
                    self.log.error(f"Photo not found: {path}")
                    return

                file = FSInputFile(path)

                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=file,
                    caption=self.template,
                )

            else:

                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=self.template,
                )

            state = self._load_state()
            state["last_sent_year"] = datetime.now().year
            self._save_state(state)

            self.log.info("March8Plugin: message sent")

        except Exception as e:
            self.log.error(f"March8Plugin send failed: {e}")

    # -------------------- CATCH UP --------------------

    async def _catch_up_if_needed(self):

        if not self.chat_id:
            return

        now = datetime.now()

        if now.month != 3 or now.day != 8:
            return

        state = self._load_state()

        if state.get("last_sent_year") == now.year:
            self.log.info("March8Plugin: already sent this year")
            return

        if (now.hour, now.minute) >= (self.hour, self.minute):
            self.log.info("March8Plugin: catch-up triggered")
            await self._send()

    # -------------------- SCHEDULE --------------------

    async def _schedule_loop(self):

        self._register_daily_job()

        await self._catch_up_if_needed()

        while True:
            schedule.run_pending()
            await asyncio.sleep(60)

    def _register_daily_job(self):

        schedule_time = f"{self.hour:02d}:{self.minute:02d}"

        def job():

            if not self.chat_id:
                return

            now = datetime.now()

            if now.month != 3 or now.day != 8:
                return

            state = self._load_state()

            if state.get("last_sent_year") == now.year:
                return

            asyncio.create_task(self._send())

        schedule.every().day.at(schedule_time).do(job)