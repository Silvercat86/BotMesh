# plugins/birthday/plugin.py

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

import schedule


from core.base_plugin import BasePlugin
from telegram_plugins.birthday.service import (
    today_almaty,
    build_payloads,
)

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from html import escape

from core.models import UniversalMessage


class BirthdayPlugin(BasePlugin):
    def __init__(
        self,
        templates: list[str],
        storage_dir: str,
        people_source: str,

        hour: int = 9,
        minute: int = 0,
        chat_id: str | None = None,
    ):
        super().__init__()

        self.required_services = ("people",)

        

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

        self.log = None

        self.people_source = people_source

        self.default_state = {
            "last_template_index": -1,
            "last_sent_for_date": "",
            "last_image_index": -1,
            "chat_id":-1,
        }

        self._schedule_task = None



    def get_actions(self) -> dict[str, Callable]:
        return {
            "birthday_test": self.birthday_test,
            "birthday_chat_status": self.birthday_chat_status,
            "birthday_register_chat": self.register_chat,
        }
    async def register_chat(self, message: UniversalMessage):


        chat_id = message.chat_id

        if self.chat_id and self.chat_id != chat_id:
            self.log.warning(f"Received chat_id {chat_id} does not match configured chat_id {self.chat_id}")
            return

        self.chat_id = chat_id

        await self._save_state({"chat_id": chat_id})

        self.log.info(f"Registered chat_id {chat_id} for birthday notifications")


    async def birthday_test(self, message: UniversalMessage):
            
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

    async def birthday_chat_status(self,message: UniversalMessage):

            


        state = await self._load_state()

        self.log.info(f"Loaded state: {state}")
        state["last_chat_status_check"] = datetime.now().isoformat()
        response = await self._save_state(state)
        self.log.info(f"save_plugin_state response: {response}")


            
        if message.chat_type != "private":
            return

        if not self.chat_id:
            await self._send(message.chat_id, "❌ chat_id не задан")
            return

        self.log.info(f"Checking bot membership for chat_id={self.chat_id}")

        bot = self.bot
        try:
            me = await bot.get_me()
            member = await bot.get_chat_member(self.chat_id, me.id)

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
    # -------------------- SETUP --------------------

    async def setup(self):

        
        self.log = logging.getLogger(f"[{self.bot_name}] birthdays")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )

        self.log.info(self.api.api_url)
        self.log.info(self.chat_id)
       

        
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


            

        

        self._schedule_task = asyncio.create_task(self._schedule_loop())



    
        

    

    # -------------------- RUN --------------------

    async def _run_today(self):
        self.log.info("Running daily birthday check")
        date = today_almaty()
        self.log.info(f"Today's date in Almaty: {date.isoformat()}")
        
        state = await self._load_state()
        self.log.info(f"Loaded state: {state}")

        

        payloads = build_payloads(
            for_date=date,
            people=self.services.people.get_people(self.people_source),
            state=state,
            templates=self.templates,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

        await self._save_state(state)

        for p in payloads:
            self.log.info(f"Birthday отправка в чат {self.chat_id}: photo={bool(p['photo'])}")
            await self._send(self.chat_id, f"{p['text']}", p["photo"])

    async def _run_test(self, test_date, chat_id: int):
        
        state = self.default_state.copy()

        self.log.info(f"Loaded state: {state}")

        

        payloads = build_payloads(
            for_date=test_date,
            people=self.services.people.get_people(self.people_source),
            state=state,
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
        state = await self._load_state()
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
