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
    today_almaty,
    load_state,
    build_payloads,
    save_state,
)
from maxapi.types import Command as MaxCommand



class WorkExperiencePlugin(BaseTelegramPlugin):
    def __init__(
        self,
        csv_path: str,
        templates_by_years: dict,
        storage_dir: str,
        people_source: str ,
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

        
        self.people_source = people_source
        self.column_map = column_map



    # ---------------- SETUP ----------------

    def setup(self):

        self.log = logging.getLogger(f"[{self.bot_name}] work_experience")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        if self.chat_file and not self.chat_id:
            self.chat_id = self._load_chat_id_from_file()


        @self.router.message(Command("register_work_chat"))
        async def register_chat(message: Message):
            if self.chat_file:
                self.chat_file.parent.mkdir(parents=True, exist_ok=True)
                self.chat_file.write_text(str(message.chat.id), encoding="utf-8")
                await message.reply("Чат зарегистрирован для стажа.")
            else:
                await message.reply("Файл чатов не настроен.")

        

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

    def _send(self, chat_id, text, photo=None):
        asyncio.create_task(
            self.adapter.send(chat_id, text, photo)
        )

    # ---------------- RUN ----------------

    async def _run_today(self):
        date = today_almaty()

        payloads = build_payloads(
            for_date=date,
            people=self.services.people.get_people(self.people_source),
            state_path=self.state_path,
            templates_by_years=self.templates_by_years,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

        for p in payloads:
            self._send(
            self.chat_id,
            f"{p['text']}",
            p["photo"],
        )
    async def _run_test(self, test_date: date, chat_id: int):
        payloads = build_payloads(
            for_date=test_date,
            people=self.services.people.get_people(self.people_source),
            state_path=self.state_path,
            templates_by_years=self.templates_by_years,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

        for p in payloads:
            self.log.info(f"TEST PAYLOAD for {test_date.isoformat()}: {p['text']} (photo: {p['photo']})")
            self._send(
            chat_id,
            f"[TEST {test_date.isoformat()}] {p['text']}",
            p["photo"],
        )


    # ---------------- SEND ----------------

    

    # ---------------- SCHEDULE ----------------

    async def _schedule_loop(self):
        self._register_job()
        await self._catch_up_if_needed()

        while True:
            schedule.run_pending()
            await asyncio.sleep(60)

    async def _catch_up_if_needed(self):
        state = load_state(self.state_path)
        self.log.info(f"Current state: {state}")

        today = today_almaty()
        self.log.info(f"Checking if we need to catch up for {today.isoformat()}")

        if state.get("last_sent_for_date") == today.isoformat():
            self.log.info("Already sent today's work experience, no catch-up needed")
            return

        now = datetime.now()
        if (now.hour, now.minute) >= (self.hour, self.minute):
            if not self.chat_id:
                self.log.warning("No chat_id configured for WorkExperiencePlugin, skipping catch-up")
                return

            
            await self._run_today()
        else:
            self.log.info("Scheduled time has not arrived yet, no catch-up needed")

    def _register_job(self):
        schedule_time = f"{self.hour:02d}:{self.minute:02d}"
        self.log.info(f"Scheduling daily work experience job at {schedule_time} Almaty time")
        def job():
            self.log.info("Running scheduled work experience job")
            if not self.chat_id:
                self.log.warning("No chat_id configured for WorkExperiencePlugin, skipping job")
                return

            
            asyncio.create_task(
                self._run_today()
            )

        schedule.every().day.at(schedule_time).do(job)

    def _load_chat_id_from_file(self):
        if not self.chat_file.exists():
            return None
        try:
            return int(self.chat_file.read_text().strip())
        except:
            return None
