# plugins/birthday/plugin.py

import asyncio
from email.mime import message
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

import schedule
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import FSInputFile


from core.base_plugin import BasePlugin
from telegram_plugins.birthday.service import (
    load_state,
    today_almaty,
    build_payloads,
)

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from html import escape

from maxapi.types import MessageCreated

from services.people_directory import Employee

from maxapi.types import Command as MaxCommand


class BirthdayPlugin(BasePlugin):
    def __init__(
        self,
        templates: list[str],
        storage_dir: str,
        people_source: str,

        hour: int = 9,
        minute: int = 0,
        dry_run: bool = False,
        chat_id: str | None = None,
        chat_file: str | None = None,
    ):
        super().__init__()

        self.required_services = ("people",)

        

        self.templates = templates

        self.hour = hour
        self.minute = minute
        self.dry_run = dry_run

        self.chat_id = chat_id
        self.chat_file = Path(chat_file) if chat_file else None

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.state_path = self.storage_dir / "birthday_state.json"
        self.images_dir = self.storage_dir / "images"
        self.external_images_dir = self.storage_dir / "images_external"

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.external_images_dir.mkdir(parents=True, exist_ok=True)

        self.log = None

        self.people_source = people_source

        

        self._schedule_task = None

    
    def get_actions(self) -> dict[str, Callable]:
        return {
            "birthday_test": self.birthday_test,
            "birthday_chat_status": self.birthday_chat_status,
        }
    

    async def birthday_test(self, message: Message):
            
            args = message.text.split()
            if len(args) < 2:
                await self._send(message.chat.id, "Нужна дата YYYY-MM-DD")
                return

            from datetime import date

            try:
                d = date.fromisoformat(args[1])
            except ValueError:
                await self._send(message.chat.id, "Неверный формат даты")
                return
            
            

            await self._run_test(d, message.chat.id)

    async def birthday_chat_status(self,message: Message):

            

        context = await self.api.get_context(message)

            
        self.log.info(context)
        if message.chat.type != "private":
            return

        if not self.chat_id:
            await self._send(message.chat.id, "❌ chat_id не задан")
            return

        self.log.info(f"Checking bot membership for chat_id={self.chat_id}")

        bot = self.bot
        try:
            me = await bot.get_me()
            member = await bot.get_chat_member(self.chat_id, me.id)

            self.log.info(f"getChatMember OK: status={member.status}")

            if member.status in ("member", "administrator","restricted"):
                await self._send(
                    message.chat.id,
                    f"✅ Бот находится в чате\n"
                    f"chat_id: `{self.chat_id}`\n"
                    f"status: `{member.status}`",
                )
            else:
                await self._send(
                    message.chat.id,
                    f"❌ Бот НЕ находится в чате\n"
                    f"chat_id: `{self.chat_id}`\n"
                    f"status: `{member.status}`",
                )

        except TelegramForbiddenError:
            await self._send(
                message.chat.id,
                f"❌ Нет доступа к чату `{self.chat_id}`\n"
                f"(бот не добавлен или был удалён)",
            )


        except TelegramBadRequest as e:
            await self._send(
                message.chat.id,
                "❌ Ошибка проверки чата\n"
                f"chat_id: <code>{self.chat_id}</code>\n"
                f"<pre>{escape(str(e))}</pre>",
            )
    # -------------------- SETUP --------------------

    def setup(self):

        
        self.log = logging.getLogger(f"[{self.bot_name}] birthdays")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )

        self.log.info(self.api.api_url)
        self.log.info(self.chat_id)
       

        if self.chat_file and not self.chat_id:
            
            self.chat_id = self._load_chat_id_from_file()


        self._schedule_task = asyncio.create_task(self._schedule_loop())



    
        

    def _load_chat_id_from_file(self) -> int | None:
        if not self.chat_file or not self.chat_file.exists():
            self.log.warning("BirthdayPlugin: chat file not found, no chat_id loaded")
            return None

        with open(self.chat_file, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            try:
                chat_id = int(line)
                self.log.info(f"BirthdayPlugin: loaded chat_id {chat_id} from file")
                return chat_id
            except ValueError:
                self.log.error(f"BirthdayPlugin: invalid chat_id in file: {line}")
                return None

    # -------------------- RUN --------------------

    async def _run_today(self):
        self.log.info("Running daily birthday check")
        date = today_almaty()
        self.log.info(f"Today's date in Almaty: {date.isoformat()}")
        
        state = load_state(self.state_path)
        self.log.info(f"Loaded state: {state}")

        

        payloads = build_payloads(
            for_date=date,
            people=self.services.people.get_people(self.people_source),
            state=state,
            state_path=self.state_path,
            templates=self.templates,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )
        for p in payloads:
            self.log.info(f"Birthday отправка в чат {self.chat_id}: photo={bool(p['photo'])}")
            await self._send(self.chat_id, f"{p['text']}", p["photo"])

    async def _run_test(self, test_date, chat_id: int):
        
        state = load_state(self.state_path)

        

        payloads = build_payloads(
            for_date=test_date,
            people=self.services.people.get_people(self.people_source),
            state=state,
            state_path=self.state_path,
            templates=self.templates,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )
        for p in payloads:
            self.log.info(f"TEST отправка в чат {chat_id}: photo={bool(p['photo'])}")
            await self._send(chat_id, f"[TEST {test_date.isoformat()}] {p['text']}", p["photo"])

    # -------------------- SEND FN --------------------

    

    # -------------------- SCHEDULE --------------------

    async def _catch_up_if_needed(self):
        state = load_state(self.state_path)
        self.log.info(state)
        today = today_almaty()

        if state.get("last_sent_for_date") == today.isoformat():
            self.log.info("BirthdayPlugin: already sent for today, no catch-up needed")
            return

        now = datetime.now()

        if (now.hour, now.minute) >= (self.hour, self.minute):
            if not self.chat_id:
                self.log.info("BirthdayPlugin: no chat_id configured, skipping catch-up")
                return

            
            self.log.info("BirthdayPlugin: catch-up needed, running daily_birthday_run for today")
            await self._run_today()
        else:
            self.log.info("No need because time")

    async def _schedule_loop(self):
        try:
            self._register_daily_job()


            await self._catch_up_if_needed()

            while True:
                schedule.run_pending()
                await asyncio.sleep(60)
        except Exception as e:
            self.log(f"Crashed: {e}")

    def _register_daily_job(self):
        schedule_time = f"{self.hour:02d}:{self.minute:02d}"

        def job():
            chat_id = self.chat_id
            if not chat_id:
                self.log.info("No chat_id")
                return

            
            asyncio.create_task(
                self._run_today(
                )
            )

        schedule.every().day.at(schedule_time).do(job)
