# plugins/employee_info/plugin.py

import logging
from multiprocessing import context

import maxapi

from core.base_plugin import BasePlugin
from core.plugin_contracts import EmployeeInfoConfig

from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from aiogram.utils.keyboard import InlineKeyboardBuilder

from typing import List


from aiogram.types import BotCommand, BotCommandScopeChat

from maxapi.types.attachments.buttons.button import Button
from maxapi.types.attachments.buttons.message_button import MessageButton
from maxapi.types import CallbackButton, MessageCreated, MessageCallback
from maxapi.enums.button_type import ButtonType
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder as MaxInlineKeyboardBuilder
from maxapi.context import MemoryContext, StatesGroup as MaxStateGroup, State as MaxState
from maxapi.types import Command as MaxCommand
from maxapi.enums.format import Format

class MaxInfoState(MaxStateGroup):
    waiting_query = MaxState()
    waiting_choice = MaxState()

class InfoState(StatesGroup):
    waiting_query = State()
    waiting_choice = State()
    


class EmployeeInfoPlugin(BasePlugin):
    required_services = ("people_directory_service",)
    config_model = EmployeeInfoConfig

    def __init__(self,sources: List[str] = [],available_nicknames : List[str] = [],available_chats : List[str] = [],scope_chats : List[int] = []):
        super().__init__()
        self.sources = sources
        self.available_nicknames = available_nicknames
        self.available_chats = available_chats
        self.scope_chats = scope_chats

    @classmethod
    def from_config(cls, config):
        sources = config.get("sources",[])
        available_nicknames = config.get("available_nicknames",[])
        available_chats = config.get("available_chats",[])
        scope_chats = config.get("scope_chats",[])

        return cls(sources,available_nicknames,available_chats,scope_chats)
        

    

    def search_people(self, people, query):

        q = query.replace("@", "").replace(" ", "").lower()

        results = []

        for p in people:

            fio = (p.fio or "").lower().replace(" ", "")
            username = (p.username or "").lower()
            phone = (p.phone or "").replace(" ", "")

            if q in fio or q == username or q in phone:
                results.append(p)

        return results



    def build_employee_text(self, p):

        if p.source == "threeit_people":

            return f"""
Сотрудник найден в базе 3IT:
<b>{p.fio}</b>

📊 Статус: {p.status or "—"}
💼 Должность: {p.position or "—"}
📦 Проект: {p.project or "—"}
👨‍💼 Руководитель: {p.manager or "—"}
🧠 Стэк: {p.stack or "—"}

📞 Телефон: {p.phone or "—"}
💬 TG: @{p.username if p.username else "—"}
✉️ Почта: {p.email or "—"}

📅 Дата выхода: {p.start_date or "—"}
🎂 День рождения: {p.birthday or "—"}
👶 Дети: {p.children or "—"}

⏱ Занятость: {p.workload or "—"}
📄 Формат: {p.employment_type or "—"}

🔥 Риск ухода: {p.risk or "—"}
📍 Зона: {p.zone or "—"}

🫱 Последняя тепловая: {p.last_heat or "—"}
📅 Следующая тепловая: {p.next_heat or "—"}

👥 Последний 1-to-1: {p.last_1to1 or "—"}
📅 Следующий 1-to-1: {p.next_1to1 or "—"}
"""
        elif p.source == "clera_people":
            return f"""
Сотрудник найден в базе Clera:
<b>{p.fio}</b>

📊 Статус: {p.status or "—"}
💼 Должность: {p.position or "—"}

📞 Телефон: {p.phone or "—"}
💬 TG: @{p.username if p.username else "—"}
✉️ Почта: {p.email or "—"}

📅 Дата выхода: {p.start_date or "—"}
🎂 День рождения: {p.birthday or "—"}

🫱 Последняя тепловая: {p.last_heat or "—"}
📅 Следующая тепловая: {p.next_heat or "—"}

👥 Последний 1-to-1: {p.last_1to1 or "—"}
📅 Следующий 1-to-1: {p.next_1to1 or "—"}
"""

        else:

            return f"""
<b>{p.fio}</b>

👤 Статус: {p.status or "—"}
💼 Должность: {p.position or "—"}
🧠 Специализация: {p.stack or "—"}

👨‍💼 Руководитель: {p.manager or "—"}
📞 Телефон: +{p.phone or "—"}
Телегрaм: {p.telegram_contact or "—"}

📅 Дата выхода: {p.start_date or "—"}
🎂 День рождения: {p.birthday or "—"}

📍 Зона: {p.zone or "—"}
⚠️ Риск ухода: {p.risk or "—"}

🏠 Точка: {p.address or "—"}
👶 Дети: {p.children or "—"}
"""

    async def register_commands(self):

        cmds = [

            BotCommand(command = "compliment", description = "Получить случайный комплиментик❤️"),
            BotCommand(command = "info", description = "Информация о сотруднике"),
        ]

        if self.scope_chats:
            await self.bot.set_my_commands(
                cmds,
                scope=BotCommandScopeChat(chat_id=self.scope_chats[0])
            )

        
        
        


        return

    async def setup(self):

        self.log = logging.getLogger(f"[{self.bot_name}] birthdays")
        if not self.log.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )

        @self.router.message(Command("chat_info"))
        async def chat_info(message: Message,state: FSMContext):
            await message.reply(f"chat id {message.chat.id}")
        
        
        

        @self.router.message(Command("info", ignore_mention=True))
        async def employee_info(message: Message, state: FSMContext):

            
            
            if message.chat.type != "private":
                if message.chat.title in self.available_chats:
                    print("available chat")
                    pass

                else:
                    if (
                        message.from_user.username
                        and message.from_user.username.lower() not in self.available_nicknames
                    ):
                        print("not available_chat+not available nick")
                        return
                    
                    print("not available_chat but available nick")

            else:
                if (
                    message.from_user.username
                    and message.from_user.username.lower() not in self.available_nicknames
                ):
                    print("not available nick in private")
                    return
                else:
                    print("available nick in private")

            

                

            await message.reply("Укажи ФИО, телефон или @username")

            await state.set_state(InfoState.waiting_query)

        @self.router.message(InfoState.waiting_query)
        async def employee_info_query(message: Message, state: FSMContext):

            query = message.text.strip()

            if not query:
                await message.reply("Укажи ФИО, телефон или @username")
                return
            
            results = []

            for source in self.sources:
                people = self.services.people.get_people(source)
                result_people = self.search_people(people,query)
                for i,p in enumerate(people):
                    self.log.info(f"{p.source} {i} {p.fio} {p.username}")
                results.extend(result_people)

            

            

            

            if not results:
                await message.reply("Сотрудник не найден")
                await state.clear()
                return

            if len(results) == 1:

                p = results[0]

                text = self.build_employee_text(p)

                await message.reply(text.strip(), parse_mode="HTML")

                await state.clear()

                return


            results = results[:5]

            builder = InlineKeyboardBuilder()

            for i, p in enumerate(results):

                birthday = getattr(p, "birthday", None)

                sources = {
                    "threeit_people": "3IT",
                    "rio_people": "RIO",
                    "clera_people": "Clera"
                }
                source = sources.get(p.source, p.source)

                button_text = f"{p.fio} {f"— {birthday}" if birthday else ''} ({source})"

                builder.button(
                    text=button_text,
                    callback_data=f"emp_{i}"
                )

            builder.adjust(1)

            await state.update_data(results=results)

            await message.reply(
                "Найдено несколько сотрудников. Уточни кто именно:",
                reply_markup=builder.as_markup()
            )

            await state.set_state(InfoState.waiting_choice)


        @self.router.callback_query(InfoState.waiting_choice)
        async def employee_choice(callback: CallbackQuery, state: FSMContext):

            data = await state.get_data()

            results = data.get("results", [])

            if not callback.data.startswith("emp_"):
                return

            index = int(callback.data.split("_")[1])

            if index >= len(results):
                await callback.answer("Ошибка выбора")
                return

            p = results[index]

            text = self.build_employee_text(p)

            await callback.message.edit_text(
                text.strip(),
                parse_mode="HTML"
            )

            await state.clear()

            await callback.answer()

        if self.dp:
            @self.dp.message_created(MaxCommand("info"))
            async def employee_info(event: MessageCreated, context: MemoryContext):
                chat_type = event.chat.type if event.chat else "no chat type"
                self.log.info(f"Chat type: {chat_type}")
                chat_title = event.chat.title if event.chat else "no chat title"
                self.log.info(f"Chat title: {chat_title}")
                self.log.info(event.from_user)
                username = event.from_user.username if event.from_user.username else event.from_user.first_name if event.from_user.first_name else "no username" 
                self.log.info(f"Username: {username}")


                if chat_type != "dialog":
                    if chat_title in self.available_chats:
                        self.log.info("available chat")
                        pass

                    else:
                        if (
                            username
                            and username.lower() not in self.available_nicknames
                        ):
                            self.log.info("not available_chat+not available nick")
                            return
                        
                        
                        self.log.info("not available_chat but available nick")

                else:
                    if (
                        username
                        and username.lower() not in self.available_nicknames
                    ):
                        self.log.info("not available nick in private")
                        return
                    else:
                        self.log.info("available nick in private")


                await event.message.reply("Укажи ФИО, телефон или @username")
                await context.set_state(MaxInfoState.waiting_query)



            @self.dp.message_created(MaxInfoState.waiting_query)
            async def employee_info_query(event: MessageCreated, context: MemoryContext):
                query = (event.message.body.text or "").strip()

                if not query:
                    await event.message.reply("Укажи ФИО, телефон или @username")
                    return

                results = []

                for source in self.sources:
                    people = self.services.people.get_people(source)
                    results.extend(self.search_people(people, query))

                if not results:
                    await event.message.reply("Сотрудник не найден")
                    await context.clear()
                    return
                
                if len(results) == 1:
                    p = results[0]
                    text = self.build_employee_text(p)

                    await event.message.reply(text, parse_mode="HTML")
                    await context.clear()
                    return
                
                results = results[:5]

                builder = MaxInlineKeyboardBuilder()

                for i, p in enumerate(results):
                    birthday = getattr(p, "birthday", None)

                    sources = {
                        "threeit_people": "3IT",
                        "rio_people": "RIO",
                        "clera_people": "Clera"
                    }
                    source = sources.get(p.source, p.source)

                    text = f"{p.fio} {f'— {birthday}' if birthday else ''} ({source})"

                    builder.row(
                        CallbackButton(
                            text=text,
                            payload=f"emp_{i}"
                        )
                    )

                await context.update_data(results=results)

                await event.message.reply(
                    "Найдено несколько сотрудников. Уточни:",
                    attachments=[builder.as_markup()]
                )

                await context.set_state(MaxInfoState.waiting_choice)
            @self.dp.message_callback(MaxInfoState.waiting_choice)
            async def employee_choice(event: MessageCallback, context: MemoryContext):
                data = await context.get_data()
                results = data.get("results", [])

                payload = event.callback.payload

                if not payload.startswith("emp_"):
                    return

                index = int(payload.split("_")[1])

                if index >= len(results):
                    return

                p = results[index]
                text = self.build_employee_text(p)

                await event.message.edit(text, attachments=[],parse_mode=Format.HTML)
                await context.clear()
