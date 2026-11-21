# plugins/work_experience/plugin.py

import asyncio
from typing import Callable

import logging
from datetime import datetime,date
from pathlib import Path

import schedule
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from core.base_plugin import BasePlugin
from core.plugin_contracts import WorkExperienceConfig
from plugins.work_experience.service import (
    today_almaty,
    build_payloads,
)
from maxapi.types import Command as MaxCommand

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from html import escape

from core.models import UniversalMessage
from maxapi.exceptions import MaxApiError

DEFAULT_WORK_TEMPLATES = {
    1 : [
        "С годом работы!"
    ]
}

class WorkExperiencePlugin(BasePlugin):
    required_services = ("people_directory_service",)
    action_contracts = {
        "work_test": {"types": ["command"]},
        "work_chat_status": {"types": ["command"]},
        "work_register_chat": {"types": ["command"]},
    }
    config_model = WorkExperienceConfig
    def __init__(
        self,
        templates_by_years: dict,
        storage_dir: str,
        people_source: str ,
        hour: int = 9,
        minute: int = 0,
        chat_id: int | None = None,
    ):
        super().__init__()
        self.scheduler = schedule.Scheduler()



        self.templates_by_years = templates_by_years

        self.hour = hour
        self.minute = minute

        self.chat_id = chat_id

        # --- storage isolation ---
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.state_path = self.storage_dir / "work_state.json"
        self.images_dir = self.storage_dir / "images"
        self.external_images_dir = self.storage_dir / "images_external"

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.external_images_dir.mkdir(parents=True, exist_ok=True)

        self.default_state = {
            "last_sent_for_date": "",
            "last_image_index": -1,
        }

        
        self.people_source = people_source

    @classmethod
    def from_config(cls, config: dict):
        templates_by_years = config["templates_by_years"]
        
        templates_by_years = {
            int(year): template
            for year, template in config["templates_by_years"].items()
        }
        
        if not templates_by_years:
            templates_by_years = DEFAULT_WORK_TEMPLATES
            

        return cls(
            templates_by_years=templates_by_years,
            storage_dir=str(config["storage_dir"]),
            people_source=str(config["people_source"]),
            hour=int(config.get("hour", 6)),
            minute=int(config.get("minute", 0)),
            chat_id=str(config["chat_id"]),
        )

    def get_actions(self) -> dict[str, Callable]:
        return {
            "work_test": self.work_test,
            "work_chat_status": self.work_chat_status,
            "work_register_chat": self.register_chat,
        }

    async def register_chat(self, message: UniversalMessage):
        chat_id = message.chat_id

        if self.chat_id and self.chat_id != chat_id:
            self.log.warning(f"Received chat_id {chat_id} does not match configured chat_id {self.chat_id}")
            return

        self.chat_id = chat_id

        await self._save_state({"chat_id": chat_id})

        self.log.info(f"Registered chat_id {chat_id} for work notifications")
    async def work_test(self, message: UniversalMessage):
            
            args = message.text.split()
            if len(args) < 2:
                await self._send(message.chat_id, "Нужна дата YYYY-MM-DD")
                return

            from datetime import date

            try:
                d = date.fromisoformat(args[1])
            except ValueError:
                await self._send(message.chat_id, "Неверный формат даты")
                return
            
            

            await self._run_test(d, message.chat_id)

    async def work_chat_status(self,message: UniversalMessage):
        if message.chat_type != "private":
            self.log.info(f"Not private chat {message.chat_type}")
            return

        if not self.chat_id:
            await self._send(message.chat_id, "❌ chat_id не задан")
            return

        self.log.info(f"Checking bot membership for chat_id={self.chat_id}")

        bot = self.bot
        try:
            me = await bot.get_me()
            id = getattr(me,"id","")
            if (id == ""):
                self.log.info("No telegram bot id")
                id = getattr(me,"user_id","")
                if (id == ""):
                    self.log.info("No max bot id")
                    
            if (id == ""):
                self.log.info("No id")
                return
            try:
                member = await bot.get_chat_member(self.chat_id, id)
                await self._send(
                    message.chat_id,
                    f"Чат доступен\n"
                )
                if 1 == 1:
                    return
            except MaxApiError as e:
                self.log.info("Нет доступа к чату (403)")
                await self._send(
                    message.chat_id,
                    f"❌ Нет доступа к чату `{self.chat_id}`\n"
                    f"code: {e.code}\n"
                    f"{e.raw.get('message')}"
                )
                return

            self.log.info(member)

            self.log.info(f"getChatMember OK: status={member.status}")

            if member.status in ("member", "administrator","restricted"):
                await self._send(
                    message.chat_id,
                    f"✅ Бот находится в чате\n"
                    f"chat_id: `{self.chat_id}`\n"
                    f"status: `{member.status}`",
                )
            else:
                await self._send(
                    message.chat_id,
                    f"❌ Бот НЕ находится в чате\n"
                    f"chat_id: `{self.chat_id}`\n"
                    f"status: `{member.status}`",
                )

        except TelegramForbiddenError:
            await self._send(
                message.chat_id,
                f"❌ Нет доступа к чату `{self.chat_id}`\n"
                f"(бот не добавлен или был удалён)",
            )


        except TelegramBadRequest as e:
            await self._send(
                message.chat_id,
                "❌ Ошибка проверки чата\n"
                f"chat_id: <code>{self.chat_id}</code>\n"
                f"<pre>{escape(str(e))}</pre>",
            )

    # ---------------- SETUP ----------------

    async def setup(self):

        self.log = logging.getLogger(f"[{self.bot_name}] work_experience")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        state = await self._load_state()
        chat_id_from_server = state.get("chat_id")
        if self.chat_id:
            self.log.info(f"Using chat_id from config {self.chat_id}")
            if chat_id_from_server != self.chat_id:
                self.log.info(f"Server chat id was different,applying new value : {self.chat_id} , old value : {chat_id_from_server}")
                await self._save_state({"chat_id":self.chat_id})
        else:
            if chat_id_from_server != -1:
                self.chat_id = chat_id_from_server
                self.log.info(f"Using chat_id from server {chat_id_from_server}")
            else:
                self.log.warning("No chat_id configured, birthday notifications will not be sent until a chat is registered")
        self._schedule_task = self.start_background_task(self._schedule_loop())

        

    async def _run_today(self):
        date = today_almaty()

        state = await self._load_state()

        payloads = build_payloads(
            for_date=date,
            people=self.services.people.get_people(self.people_source),
            state=state,
            templates_by_years=self.templates_by_years,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

        await self._save_state(state)

        for p in payloads:
            await self._send(
            self.chat_id,
            f"{p['text']}",
            p["photo"],
        )
    async def _run_test(self, test_date: date, chat_id: int):
        state = self.default_state.copy()
        payloads = build_payloads(
            for_date=test_date,
            people=self.services.people.get_people(self.people_source),
            state=state,
            templates_by_years=self.templates_by_years,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )
        self.log.info(len(payloads))

        for p in payloads:
            self.log.info(f"TEST PAYLOAD for {test_date.isoformat()} (photo: {p['photo']})")
            await self._send(
            chat_id,
            f"[TEST {test_date.isoformat()}] {p['text']}",
            p["photo"],
        )



    

    # ---------------- SCHEDULE ----------------

    async def _schedule_loop(self):
        self._register_job()
        await self._catch_up_if_needed()

        while True:
            self.scheduler.run_pending()
            await asyncio.sleep(60)

    async def _catch_up_if_needed(self):
        state = await self._load_state()
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

            
            self.start_background_task(
                self._run_today()
            )

        self.scheduler.every().day.at(schedule_time).do(job)

    def _load_chat_id_from_file(self):
        if not self.chat_file.exists():
            return None
        try:
            return int(self.chat_file.read_text().strip())
        except:
            return None
