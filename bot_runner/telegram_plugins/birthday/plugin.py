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
                await message.reply("❌ chat_id не задан")
                return

            self.log.info(f"Checking bot membership for chat_id={self.chat_id}")

            bot = self.bot
            try:
                me = await bot.get_me()
                member = await bot.get_chat_member(self.chat_id, me.id)

                self.log.info(f"getChatMember OK: status={member.status}")

                if member.status in ("member", "administrator","restricted"):
                    await message.reply(
                        f"✅ Бот находится в чате\n"
                        f"chat_id: `{self.chat_id}`\n"
                        f"status: `{member.status}`",
                        parse_mode="HTML",
                    )
                else:
                    await message.reply(
                        f"❌ Бот НЕ находится в чате\n"
                        f"chat_id: `{self.chat_id}`\n"
                        f"status: `{member.status}`",
                        parse_mode="HTML",
                    )

            except TelegramForbiddenError:
                await message.reply(
                    f"❌ Нет доступа к чату `{self.chat_id}`\n"
                    f"(бот не добавлен или был удалён)",
                    parse_mode="HTML",
                )


            except TelegramBadRequest as e:
                await message.reply(
                    "❌ Ошибка проверки чата\n"
                    f"chat_id: <code>{self.chat_id}</code>\n"
                    f"<pre>{escape(str(e))}</pre>",
                    parse_mode="HTML",
                )

        @self.router.message(Command("birthday_test"))
        async def birthday_test(message: Message):
            args = message.text.split()
            if len(args) < 2:
                await message.reply("Нужна дата YYYY-MM-DD")
                return

            from datetime import date

            try:
                d = date.fromisoformat(args[1])
            except ValueError:
                await message.reply("Неверный формат даты")
                return

            await self._run_test(d, message.chat.id)

        self._schedule_task = asyncio.create_task(self._schedule_loop())
        # @self.router.message(Command("register_birthday_chat"))
        # async def register_birthday_chat(message: Message):
        #     if message.chat.type == "private":
        #         await message.delete()
        #         return

        #     chat_id = message.chat.id
        #     self.chat_id = chat_id

        #     if self.chat_file:
        #         with open(self.chat_file, "w", encoding="utf-8") as f:
        #             f.write(str(chat_id))

        #     await message.reply(f"✅ Зарегистрирован chat_id: `{chat_id}`", parse_mode="HTML")
        

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

    # -------------------- SEND FN --------------------


    def _make_send_fn(self):

        async def async_send(chat_id: int, text: str, photo: str | None):
            bot = self.bot

            if self.dry_run:
                print("[DRY]", text)
                return

            if photo:
                file = FSInputFile(photo)
                await bot.send_photo(chat_id, photo=file, caption=text)
            else:
                await bot.send_message(chat_id, text)
        def send(chat_id, text, photo=None):
            asyncio.create_task(async_send(chat_id, text, photo))

        return send

    # -------------------- SCHEDULE --------------------

    async def _catch_up_if_needed(self):
        state = load_state(self.state_path)
        today = today_almaty()

        # если уже отправляли — ничего не делаем
        if state.get("last_sent_for_date") == today.isoformat():
            self.log.info("BirthdayPlugin: already sent for today, no catch-up needed")
            return

        now = datetime.now()
        if (now.hour, now.minute) >= (self.hour, self.minute):
            if not self.chat_id:
                self.log.info("BirthdayPlugin: no chat_id configured, skipping catch-up")
                return

            send_fn = self._make_send_fn()
            self.log.info("BirthdayPlugin: catch-up needed, running daily_birthday_run for today")
            # people = self.services.people.get_people("birthdays_test_three")
            daily_birthday_run(
                send_fn=send_fn,
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

        schedule.every().day.at(schedule_time).do(job)
