# plugins/birthday/max_plugin.py

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import maxapi
import schedule


from core.base_plugin import BaseMaxPlugin
from maxapi.types import MessageCreated

from telegram_plugins.birthday.service import (
    daily_birthday_run,
    test_birthday_run,
    load_state,
    today_almaty,
)


class MaxBirthdayPlugin(BaseMaxPlugin):
    def __init__(
        self,
        csv_path: str,
        templates: list[str],
        storage_dir: str,
        hour: int = 9,
        minute: int = 0,
        chat_id: int | None = None,
    ):
        super().__init__()

        self.required_services = ("people",)

        self.csv_path = csv_path
        self.templates = templates

        self.hour = hour
        self.minute = minute
        self.chat_id = chat_id

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.state_path = self.storage_dir / "birthday_state.json"

        self.images_dir = self.storage_dir / "images"
        self.external_images_dir = self.storage_dir / "images_external"

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.external_images_dir.mkdir(parents=True, exist_ok=True)

        self.log = logging.getLogger("max_birthdays")



    # -------------------- SETUP --------------------

    def setup(self):

        self.log.info("Setting up MaxBirthdayPlugin")

        @self.dp.message_created()
        async def handle_commands(event: MessageCreated):
            self.log.info(f"Received message: {event.message.body.text}")
            text = event.message.body.text or ""

            if text.startswith("/birthday_test"):
                self.log.info("Running birthday test command")
                parts = text.split()
                if len(parts) < 2:
                    self.log.warning("No date provided for birthday test command")
                    return

                from datetime import date

                try:
                    d = date.fromisoformat(parts[1])
                    self.log.info(f"Parsed date for test command: {d}")
                except:
                    self.log.warning(f"Failed to parse date from command: {parts[1]}")
                    return

                await self._run_test(d, event.chat.chat_id)

        asyncio.create_task(self._schedule_loop())

    # -------------------- RUN --------------------

    async def _run_today(self, chat_id: int):
        send_fn = self._make_send_fn()

        daily_birthday_run(
            send_fn=send_fn,
            chat_id=chat_id,
            csv_path=self.csv_path,
            templates=self.templates,
            state_path=self.state_path,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

    async def _run_test(self, test_date, chat_id: int):
        send_fn = self._make_send_fn()

        test_birthday_run(
            send_fn=send_fn,
            test_date=test_date,
            chat_id=chat_id,
            csv_path=self.csv_path,
            templates=self.templates,
            state_path=self.state_path,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

    # -------------------- SEND --------------------

    def _make_send_fn(self):
        async def async_send(chat_id: int, text: str, photo: str | None):
            await self.bot.send_message(chat_id=chat_id, text=text,attachments=[maxapi.types.InputMedia(photo)] if photo else None)

        def send(chat_id, text, photo=None):
            asyncio.create_task(async_send(chat_id, text, photo))

        return send

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

            send_fn = self._make_send_fn()

            daily_birthday_run(
                send_fn=send_fn,
                chat_id=self.chat_id,
                csv_path=self.csv_path,
                templates=self.templates,
                state_path=self.state_path,
                images_dir=self.images_dir,
                external_images_dir=self.external_images_dir,
            )

        schedule.every().day.at(schedule_time).do(job)

    async def _catch_up_if_needed(self):
        state = load_state(self.state_path)
        today = today_almaty()

        self.log.info(f"Checking if catch-up is needed. Last sent for date: {state.get('last_sent_for_date')}, today: {today.isoformat()}")

        if state.get("last_sent_for_date") == today.isoformat():
            self.log.info("Already sent for today, no catch-up needed")
            return

        now = datetime.now()
        if (now.hour, now.minute) >= (self.hour, self.minute):
            self.log.info("Catch-up needed, running daily_birthday_run for today")
            if not self.chat_id:
                self.log.info("No chat_id configured, skipping catch-up")
                return

            send_fn = self._make_send_fn()

            daily_birthday_run(
                send_fn=send_fn,
                chat_id=self.chat_id,
                csv_path=self.csv_path,
                templates=self.templates,
                state_path=self.state_path,
                images_dir=self.images_dir,
                external_images_dir=self.external_images_dir,
            )
        self.log.info("Catch-up check complete")