# plugins/birthday/plugin.py

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import schedule
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import FSInputFile


from core.base_plugin import BaseTelegramPlugin
from telegram_plugins.birthday.service import (
    daily_birthday_run,
    test_birthday_run,
    load_state,
    today_almaty,
)

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from html import escape




class BirthdayPlugin(BaseTelegramPlugin):
    def __init__(
        self,
        csv_path: str,
        templates: list[str],
        storage_dir: str,
        hour: int = 9,
        minute: int = 0,
        dry_run: bool = False,
        chat_id: int | None = None,
        chat_file: str | None = None,
    ):
        super().__init__()

        self.required_services = ("people",)

        

        self.csv_path = csv_path
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

        

        self._schedule_task = None

    def _send(self, chat_id, text, photo=None):
                asyncio.create_task(
                    self.adapter.send(chat_id, text, photo)
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
       

        if self.chat_file:
            self.chat_id = self._load_chat_id_from_file()

        

        @self.router.message(Command("birthday_chat_status"))
        async def birthday_chat_status(message: Message):

            

            context = await self.api.get_context(message)

            
            self.log.info(context)
            if message.chat.type != "private":
                return

            if not self.chat_id:
                await self.adapter.send(message.chat.id, "❌ chat_id не задан")
                return

            self.log.info(f"Checking bot membership for chat_id={self.chat_id}")

            bot = self.bot
            try:
                me = await bot.get_me()
                member = await bot.get_chat_member(self.chat_id, me.id)

                self.log.info(f"getChatMember OK: status={member.status}")

                if member.status in ("member", "administrator","restricted"):
                    await self.adapter.send(
                        message.chat.id,
                        f"✅ Бот находится в чате\n"
                        f"chat_id: `{self.chat_id}`\n"
                        f"status: `{member.status}`",
                    )
                else:
                    await self.adapter.send(
                        message.chat.id,
                        f"❌ Бот НЕ находится в чате\n"
                        f"chat_id: `{self.chat_id}`\n"
                        f"status: `{member.status}`",
                    )

            except TelegramForbiddenError:
                await self.adapter.send(
                    message.chat.id,
                    f"❌ Нет доступа к чату `{self.chat_id}`\n"
                    f"(бот не добавлен или был удалён)",
                )


            except TelegramBadRequest as e:
                await self.adapter.send(
                    message.chat.id,
                    "❌ Ошибка проверки чата\n"
                    f"chat_id: <code>{self.chat_id}</code>\n"
                    f"<pre>{escape(str(e))}</pre>",
                )

        @self.router.message(Command("birthday_test"))
        async def birthday_test(message: Message):
            
            args = message.text.split()
            if len(args) < 2:
                await self.adapter.send(message.chat.id, "Нужна дата YYYY-MM-DD")
                return

            from datetime import date

            try:
                d = date.fromisoformat(args[1])
            except ValueError:
                await self.adapter.send(message.chat.id, "Неверный формат даты")
                return

            await self._run_test(d, message.chat.id)

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

    async def _run_today(self, chat_id: int):
        
        
        daily_birthday_run(
            send_fn=self._send,
            chat_id=chat_id,
            csv_path=self.csv_path,
            templates=self.templates,
            state_path=self.state_path,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

    async def _run_test(self, test_date, chat_id: int):
        
        test_birthday_run(
            send_fn=self._send,
            test_date=test_date,
            chat_id=chat_id,
            csv_path=self.csv_path,
            templates=self.templates,
            state_path=self.state_path,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )

    # -------------------- SEND FN --------------------

    

    # -------------------- SCHEDULE --------------------

    async def _catch_up_if_needed(self):
        state = load_state(self.state_path)
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
            daily_birthday_run(
                send_fn=self._send,
                chat_id=self.chat_id,
                csv_path=self.csv_path,
                templates=self.templates,
                state_path=self.state_path,
                images_dir=self.images_dir,
                external_images_dir=self.external_images_dir,
            )

    async def _schedule_loop(self):
        self._register_daily_job()

        await self._catch_up_if_needed()

        while True:
            schedule.run_pending()
            await asyncio.sleep(60)

    def _register_daily_job(self):
        schedule_time = f"{self.hour:02d}:{self.minute:02d}"

        def job():
            chat_id = self.chat_id
            if not chat_id:
                return

            
            daily_birthday_run(
                send_fn=self._send,
                chat_id=chat_id,
                csv_path=self.csv_path,
                templates=self.templates,
                state_path=self.state_path,
                images_dir=self.images_dir,
                external_images_dir=self.external_images_dir,
            )

        schedule.every().day.at(schedule_time).do(job)
