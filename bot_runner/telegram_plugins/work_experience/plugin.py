# plugins/work_experience/plugin.py

import asyncio
import logging
from datetime import datetime,date
from pathlib import Path

import schedule
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from core.base_plugin import BaseTelegramPlugin
from telegram_plugins.work_experience.service import (
    daily_work_experience_run,
    today_almaty,
    load_state,
)



class WorkExperiencePlugin(BaseTelegramPlugin):
    def __init__(
        self,
        csv_path: str,
        templates_by_years: dict,
        storage_dir: str,
        column_map: dict = None,
        hour: int = 9,
        minute: int = 0,
        dry_run: bool = False,
        chat_id: int | None = None,
        chat_file: str | None = None,
    ):
        super().__init__()

        self.required_services = ("people",)


        self.csv_path = csv_path
        self.templates_by_years = templates_by_years

        self.hour = hour
        self.minute = minute
        self.dry_run = dry_run

        self.chat_id = chat_id
        self.chat_file = Path(chat_file) if chat_file else None

        # --- storage isolation ---
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.state_path = self.storage_dir / "work_state.json"
        self.images_dir = self.storage_dir / "images"
        self.external_images_dir = self.storage_dir / "images_external"

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.external_images_dir.mkdir(parents=True, exist_ok=True)

        

        self.column_map = column_map



    # ---------------- SETUP ----------------

    def setup(self):

        self.log = logging.getLogger(f"[{self.bot_name}] work_experience")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        if self.chat_file:
            self.chat_id = self._load_chat_id_from_file()


        @self.router.message(Command("register_work_chat"))
        async def register_chat(message: Message):
            if self.chat_file:
                self.chat_file.parent.mkdir(parents=True, exist_ok=True)
                self.chat_file.write_text(str(message.chat.id), encoding="utf-8")
                await message.reply("Чат зарегистрирован для стажа.")
            else:
                await message.reply("Файл чатов не настроен.")

        @self.router.message(Command("work_today"))
        async def work_today(message: Message):
            await self._run_today(message.chat.id)

        @self.router.message(Command("work_test"))
        async def work_test(message: Message):
            args = message.text.split()

            if len(args) < 2:
                await message.reply("Нужна дата YYYY-MM-DD")
                return

            try:
                d = date.fromisoformat(args[1])
            except ValueError:
                await message.reply("Неверный формат даты")
                return
            await self._run_test(d, message.chat.id)

        asyncio.create_task(self._schedule_loop())

    # ---------------- RUN ----------------

    async def _run_today(self, chat_id: int):
        send_fn = self._make_send_fn()

        daily_work_experience_run(
            send_fn=send_fn,
            chat_id=chat_id,
            csv_path=self.csv_path,
            templates_by_years=self.templates_by_years,
            state_path=self.state_path,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
            column_map=self.column_map,
        )
    async def _run_test(self, test_date: date, chat_id: int):
        send_fn = self._make_send_fn()

        from plugins.work_experience.service import test_work_experience_run

        test_work_experience_run(
            send_fn=send_fn,
            test_date=test_date,
            chat_id=chat_id,
            csv_path=self.csv_path,
            templates_by_years=self.templates_by_years,
            state_path=self.state_path,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
            column_map=self.column_map,
        )


    # ---------------- SEND ----------------

    def _make_send_fn(self):
        async def async_send(chat_id: int, text: str, photo: str | None):
            try:
                if self.dry_run:
                    print("[DRY]", text)
                    return

                if photo:
                    file = FSInputFile(photo)
                    await self.bot.send_photo(chat_id, photo=file, caption=text)
                else:
                    await self.bot.send_message(chat_id, text)

            except Exception as e:
                self.log.exception(f"Ошибка отправки стажа: {e}")

        def send(chat_id, text, photo=None):
            asyncio.create_task(async_send(chat_id, text, photo))

        return send

    # ---------------- SCHEDULE ----------------

    async def _schedule_loop(self):
        self._register_job()
        await self._catch_up_if_needed()

        while True:
            schedule.run_pending()
            await asyncio.sleep(60)

    async def _catch_up_if_needed(self):
        state = load_state(self.state_path)
        self.log.info(state)

        today = today_almaty()

        if state.get("last_sent_for_date") == today.isoformat():
            return

        now = datetime.now()
        if (now.hour, now.minute) >= (self.hour, self.minute):
            if not self.chat_id:
                return

            send_fn = self._make_send_fn()
            daily_work_experience_run(
                send_fn=send_fn,
                chat_id=self.chat_id,
                csv_path=self.csv_path,
                templates_by_years=self.templates_by_years,
                state_path=self.state_path,
                images_dir=self.images_dir,
                external_images_dir=self.external_images_dir,
                column_map=self.column_map,
            )

    def _register_job(self):
        schedule_time = f"{self.hour:02d}:{self.minute:02d}"
        self.log.info(f"Scheduling daily work experience job at {schedule_time} Almaty time")
        def job():
            self.log.info("Running scheduled work experience job")
            if not self.chat_id:
                self.log.warning("No chat_id configured for WorkExperiencePlugin, skipping job")
                return

            send_fn = self._make_send_fn()
            daily_work_experience_run(
                send_fn=send_fn,
                chat_id=self.chat_id,
                csv_path=self.csv_path,
                templates_by_years=self.templates_by_years,
                state_path=self.state_path,
                images_dir=self.images_dir,
                external_images_dir=self.external_images_dir,
                column_map=self.column_map,
            )

        schedule.every().day.at(schedule_time).do(job)

    def _load_chat_id_from_file(self):
        if not self.chat_file.exists():
            return None
        try:
            return int(self.chat_file.read_text().strip())
        except:
            return None
