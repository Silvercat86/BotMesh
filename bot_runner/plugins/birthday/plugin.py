# plugins/birthday/plugin.py

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

import schedule


from core.base_plugin import BasePlugin
from core.plugin_contracts import BirthdayConfig
from plugins.birthday.service import (
    today_almaty,
    build_payloads,
)

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from html import escape

from core.models import UniversalMessage

from maxapi.exceptions import MiddlewareException
from maxapi.exceptions import MaxApiError

DEFAULT_BIRTHDAY_TEMPLATES = [
    "{mention}, от всего сердца поздравляем с Днем рождения! 🎉\n"
    "От всего нашего дружного коллектива желаем крепкого здоровья, внутреннего спокойствия, "
    "ярких событий и уверенности в завтрашнем дне. Пусть каждый новый день приносит больше радости, "
    "тепла, вдохновения и приятных поводов для улыбки. Пусть рядом будут надежные люди, "
    "а в доме всегда царят уют, гармония и душевное равновесие!",

    "{mention}, поздравляем с Днем рождения! 🎂\n"
    "Желаем, чтобы этот год был наполнен удачными решениями, хорошими новостями и важными победами. "
    "Пусть дела складываются легко, планы реализуются вовремя, а сил хватает не только на работу, "
    "но и на отдых, близких, мечты и все, что приносит настоящую радость.",

    "{mention}, от всего нашего коллектива — самые искренние поздравления с Днем рождения! 🌟\n"
    "Пусть впереди будет много светлых дней, интересных возможностей и приятных перемен. "
    "Желаем здоровья, стабильности, душевного тепла и уверенности в собственных силах. "
    "Пусть каждый этап жизни приносит ценный опыт, вдохновение и ощущение, что все движется в правильном направлении.",

    "{mention}, поздравляем с Днем рождения! 🎈\n"
    "Желаем, чтобы в жизни всегда находилось место для радости, спокойствия и новых впечатлений. "
    "Пусть работа приносит достойные результаты, отдых действительно восстанавливает силы, "
    "а рядом будут люди, с которыми легко, надежно и тепло. Крепкого здоровья, удачи и благополучия!",

    "{mention}, с Днем рождения! 🌺\n"
    "От всего коллектива желаем, чтобы жизнь радовала яркими красками, добрыми встречами "
    "и приятными событиями. Пусть каждый день приносит ощущение гармонии, а все важные цели "
    "постепенно становятся реальностью. Желаем уверенности, внутренней силы и много поводов для счастья.",

    "{mention}, поздравляем с Днем рождения! ✨\n"
    "Пусть удача сопровождает во всех начинаниях, а каждый новый день открывает что-то хорошее. "
    "Желаем крепкого здоровья, стабильного благополучия, интересных задач и теплых моментов, "
    "которые хочется вспоминать с улыбкой. Пусть в жизни будет больше свободы, вдохновения и радости.",

    "{mention}, с Днем рождения! 🎊\n"
    "От всей команды желаем, чтобы все вложенные усилия возвращались достойными результатами, "
    "уважением и внутренним удовлетворением. Пусть вдохновение приходит легко, дела спорятся, "
    "а в расписании всегда находится место для отдыха, близких и личного пространства. "
    "Береги себя, свое здоровье и душевное тепло.",

    "{mention}, поздравляем с Днем рождения! 🌸\n"
    "Желаем идеального баланса между делами, отдыхом и тем, что по-настоящему наполняет энергией. "
    "Пусть новые цели достигаются спокойно и уверенно, а дома всегда ждут тепло, уют и поддержка. "
    "Пусть в жизни будет больше простых радостей, приятных сюрпризов и счастливых моментов.",

    "{mention}, с Днем рождения! 💼✨\n"
    "От лица всей команды желаем уверенности в своих силах, финансовой стабильности, "
    "интересных возможностей и надежной поддержки рядом. Пусть каждый новый год жизни становится "
    "более осознанным, насыщенным и благополучным. Пусть мечты превращаются в планы, "
    "а планы — в реальные достижения.",

    "{mention}, от всего нашего дружного коллектива — поздравляем с Днем рождения! 🎁\n"
    "Пусть добро, внимание и энергия, которые ты вкладываешь в каждый день, возвращаются вдвойне. "
    "Желаем крепкого здоровья, спокойствия в душе, удачи в делах и исполнения личных желаний. "
    "Пусть впереди будет много хороших новостей, теплых встреч и моментов, которые делают жизнь счастливее.",

    "{mention}, с праздником! 🌈\n"
    "Желаем, чтобы жизнь складывалась в гармоничную, цельную и светлую картину. "
    "Пусть сложности решаются легче, планы становятся понятнее, а каждый день приносит что-то доброе. "
    "Новых побед, внутренней уверенности, крепкого здоровья и много счастливых моментов в наступающем году!",

    "{mention}, в День рождения от всего коллектива желаем, "
    "чтобы вся положительная энергия, вложенная в дела, отношения и важные цели, "
    "возвращалась добром, здоровьем и благополучием. 🌞\n"
    "Пусть каждый день приносит ощущение смысла, а дома ждут любовь, поддержка и спокойствие. "
    "Желаем вдохновения, стабильности и светлого настроения!",

    "{mention}, от всей души поздравляем с Днем рождения! 💖\n"
    "Пусть этот год будет ярким, насыщенным хорошими событиями, новыми открытиями и приятными переменами. "
    "Желаем легкости в начинаниях, порядка в делах, тепла в сердце и уверенности в будущем. "
    "Пусть рядом будут люди, с которыми спокойно и радостно, а каждый день дает повод улыбнуться."
]


class BirthdayPlugin(BasePlugin):
    required_services = ("people_directory_service",)
    action_contracts = {
        "birthday_test": {"types": ["command"]},
        "birthday_chat_status": {"types": ["command"]},
        "birthday_register_chat": {"types": ["command"]},
    }
    config_model = BirthdayConfig
    def __init__(
        self,
        templates_name: str,
        storage_dir: str,
        people_source: str,

        hour: int = 9,
        minute: int = 0,
        chat_id: str | None = None,
    ):
        super().__init__()


        
        self.templates_name = templates_name

        self.templates : list[str] = None

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

    @classmethod
    def from_config(cls, config: dict):
        templates_name = config["templates"]
        return cls(
            templates_name=templates_name,
            storage_dir=str(config["storage_dir"]),
            people_source=str(config["people_source"]),
            hour=int(config.get("hour", 6)),
            minute=int(config.get("minute", 0)),
            chat_id=str(config["chat_id"]),
        )



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
                await self._send(message.chat_id, "Нужна дата YYYY-MM-DD")
                return

            from datetime import date

            try:
                d = date.fromisoformat(args[1])
            except ValueError:
                await self._send(message.chat_id, "Неверный формат даты")
                return
            
            

            await self._run_test(d, message.chat_id)

    async def birthday_chat_status(self,message: UniversalMessage):
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
        

    # -------------------- SETUP --------------------

    async def setup(self):

        
        self.log = logging.getLogger(f"[{self.bot_name}] birthdays")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )

       

        
        state = await self._load_state()
        chat_id_from_server = state.get("chat_id")
        if self.chat_id:
            if chat_id_from_server != self.chat_id:
                await self._save_state({"chat_id":self.chat_id})
        else:
            if chat_id_from_server != -1:
                self.chat_id = chat_id_from_server
            else:
                self.log.warning("No chat_id configured, birthday notifications will not be sent until a chat is registered")

        try :

            template_pack = await self.get_template_pack(self.templates_name)
            data = template_pack.get("data")
            if (data):
                self.templates = data
            else:
                self.log.warning(f"Templates for {self.name} {self.bot_name} were empty")
                self.templates = DEFAULT_BIRTHDAY_TEMPLATES


        except Exception as e:
            self.log.warning(f"Couldnt find templates for {self.name} {self.bot_name}")
            self.templates = DEFAULT_BIRTHDAY_TEMPLATES

            

        

        self._schedule_task = asyncio.create_task(self._schedule_loop())



    
        

    

    # -------------------- RUN --------------------

    async def _run_today(self):
        date = today_almaty()
        
        state = await self._load_state()

        

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
            await self._send(self.chat_id, f"{p['text']}", p["photo"])

    async def _run_test(self, test_date, chat_id: int):
        
        state = self.default_state.copy()


        

        payloads = build_payloads(
            for_date=test_date,
            people=self.services.people.get_people(self.people_source),
            state=state,
            templates=self.templates,
            images_dir=self.images_dir,
            external_images_dir=self.external_images_dir,
        )


        for p in payloads:
            await self._send(chat_id, f"[TEST {test_date.isoformat()}] {p['text']}", p["photo"])

    # -------------------- SEND FN --------------------

    

    # -------------------- SCHEDULE --------------------

    async def _catch_up_if_needed(self):
        state = await self._load_state()
        today = today_almaty()

        if state.get("last_sent_for_date") == today.isoformat():
            return

        now = datetime.now()

        if (now.hour, now.minute) >= (self.hour, self.minute):
            if not self.chat_id:
                return

            
            await self._run_today()
       

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
