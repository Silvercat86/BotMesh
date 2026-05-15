import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import Router


from core.bot_instance import TelegramBotInstance
from core.bot_instance import MaxBotInstance

from telegram_plugins.compliment.plugin import ComplimentPlugin
from telegram_plugins.birthday.plugin import BirthdayPlugin
from telegram_plugins.work_experience.plugin import WorkExperiencePlugin
from telegram_plugins.welcome.plugin import WelcomePlugin
from telegram_plugins.start.plugin import StartPlugin
from telegram_plugins.memes.plugin import MemePlugin
from telegram_plugins.march8.plugin import March8Plugin
from telegram_plugins.employee_info.plugin import EmployeeInfoPlugin
from telegram_plugins.clever_shma.plugin import CleverShmaPlugin


from core.templates import RIO_BIRTHDAY_TEMPLATES, THREEIT_BIRTHDAY_TEMPLATES
from core.templates import RIO_WORK_TEMPLATES, THREEIT_WORK_TEMPLATES
from core.templates import THREEIT_WELCOME_TEMPLATE, THREEIT_WELCOME_QUESTIONS
from core.templates import RIO_WELCOME_TEMPLATE, RIO_WELCOME_QUESTIONS
from core.templates import CLERA_WELCOME_TEMPLATE,CLERA_WELCOME_QUESTIONS
from core.templates import RIO_START_TEMPLATES, THREEIT_START_TEMPLATES,CLERA_START_TEMPLATES
from core.templates import RIO_MARCH8_TEMPLATE, THREEIT_MARCH8_TEMPLATE


from services.people_directory import PeopleDirectoryService

from core.action import Action, ActionType




load_dotenv()

is_testing = os.getenv("TESTING", "false").lower() == "true"


async def main() -> None:
    if not is_testing:

        not_shma_bot_instance = TelegramBotInstance(
            token=os.getenv("NOT_SHMA_BOT_TOKEN", ""),
            api_key=os.getenv("NOT_SHMA_API_KEY",""),
            name="NotShmaBot",
            plugins=[
                CleverShmaPlugin(),
            ],
            services=[]
        )

        rio_bot_instance = TelegramBotInstance(
            token=os.getenv("RIO_BOT_TOKEN", ""),
            api_key=os.getenv("RIO_API_KEY",""),
            name="RioBot",
            plugins=[
                ComplimentPlugin(),
                BirthdayPlugin(
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/rio/birthday",
                    people_source="rio_people_birthdays",
                    hour=6,
                    minute=0,
                    chat_id="-1001712668166"
                ),
                WorkExperiencePlugin(
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/rio/work",
                    people_source="rio_people_work",
                    hour=6,
                    minute=0,
                    chat_id="-1001712668166"
                ),

                WelcomePlugin(
                    base_template=RIO_WELCOME_TEMPLATE,
                    questions=RIO_WELCOME_QUESTIONS,
                    n_questions=3,
                    ),

                StartPlugin(
                    messages=RIO_START_TEMPLATES
                ),
                # MemePlugin(),
                March8Plugin(
                    template=RIO_MARCH8_TEMPLATE,
                    storage_dir="data/rio/march8",
                    hour=6,
                    minute=0,
                    photo = "data/rio/march8/image.jpg",
                    chat_id="-1001712668166"

                ),

                EmployeeInfoPlugin(
                    sources=["rio_people"],
                    available_nicknames=["not_silvercat86","katyalay7","kseniyanika","olga_voropaeva","jenay1985","kamilkamimiko","antonvrp","cheerryplum"],
                    available_chats=["Забота Рио 2025","test"],
                    scope_chats = [-1003575870359]
                
                ),

            ],
            services=[
                PeopleDirectoryService(
                    sources={
                         "rio_people_birthdays": {
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "birthday": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people_work": {
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "start_date": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people": {
                            "url": "https://docs.google.com/spreadsheets/d/11xOQjQxoYvfbyOAu5oPtR0SE6xkgCFJY7Q0_Zt1ShuY/export?format=csv",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode": "named",
                            "required_fields": ("fio",),
                            "fields_mapping": {

                                # база
                                "fio": "ФИО",
                                "status": "Статус",
                                "position": "Должность",

                                # занятость / hr
                                "employment_type": "формат трудоустройства",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                # даты
                                "start_date": "дата выхода",
                                "birthday": "день рождения",
                                "probation_end": "окончание ИС",

                                # тепловые / встречи (исправлены названия)
                                "last_heat": "Дата посл  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",

                                "last_1to1": "Дата посл 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",

                                # hr данные
                                "employee_card": "Карточка сотрдуника",

                                # человек
                                "gender": "пол",
                                "stack": "Специализация",

                                # орг структура
                                "manager": "Руководитель",
                                "project": "Точка",  # тут спорно, но лучше чем терять поле

                                # контакты
                                "phone": "Телефон",
                                "telegram_contact": "Телеграм",

                                # доп
                                "children": "дети",
                                "address": "адрес проживания",

                                # медиа
                                "photo_url": "фото для поздравления",
                            }
                        },
                    },
                    cache_ttl=300,
                )
            ],
            actions=[
                Action(name="birthday_test", func_name="birthday_test", scope="private", type=ActionType.COMMAND),
                Action(name="birthday_chat_status", func_name="birthday_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="user_join", func_name="handle_chat_member_join", scope="private", type=ActionType.CHAT_MEMBER_JOIN),
                Action(name="register_birthday_chat", func_name="birthday_register_chat", scope="private", type=ActionType.COMMAND),
                Action(name="work_test", func_name="work_test", scope="private", type=ActionType.COMMAND),
                Action(name="work_chat_status", func_name="work_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="register_work_chat", func_name="work_register_chat", scope="private", type=ActionType.COMMAND),
            ],
        )

        

        keepcat_bot_instance = TelegramBotInstance(
            token=os.getenv("KEEPCAT_BOT_TOKEN", ""),
            api_key=os.getenv("KEEPCAT_API_KEY",""),
            name="KeepCatBot",
            plugins=[
                StartPlugin(
                    messages=RIO_START_TEMPLATES
                ),
            ],
            services=[
                PeopleDirectoryService(
                    sources={},
                        
                    cache_ttl=300,
                        

                )]
        )
        clera_bot_instance = TelegramBotInstance(
            token=os.getenv("CLERA_BOT_TOKEN", ""),
            api_key=os.getenv("CLERA_API_KEY",""),

            name="CleraBot",
            plugins=[
                WelcomePlugin(CLERA_WELCOME_TEMPLATE,
                              CLERA_WELCOME_QUESTIONS,
                              ),
                StartPlugin(CLERA_START_TEMPLATES),
            ],
            services=[
                ],
            actions=[
                # Action(name="birthday_test", func_name="birthday_test", scope="private", type=ActionType.COMMAND),
                # Action(name="birthday_chat_status", func_name="birthday_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="user_join", func_name="handle_chat_member_join", scope="private", type=ActionType.CHAT_MEMBER_JOIN),
                # Action(name="register_birthday_chat", func_name="birthday_register_chat", scope="private", type=ActionType.COMMAND),
                # Action(name="work_test", func_name="work_test", scope="private", type=ActionType.COMMAND),
                # Action(name="work_chat_status", func_name="work_chat_status", scope="private", type=ActionType.COMMAND),
                # Action(name="register_work_chat", func_name="work_register_chat", scope="private", type=ActionType.COMMAND),
            ],
        )

        rio_max_bot_instance = MaxBotInstance(
            token=os.getenv("RIO_MAX_BOT_TOKEN", ""),
            api_key=os.getenv("RIO_MAX_API_KEY",""),
            name="RioMaxBot",
            plugins=[
                BirthdayPlugin(
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/rio/max/birthday",
                    people_source="rio_people_birthdays",
                    hour=6,
                    minute=0,
                    chat_id="-72336909860345",
                ),
                WorkExperiencePlugin(
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/rio/max/work",
                    people_source="rio_people_work",
                    hour=6,
                    minute=0,
                    chat_id="-72336909860345"
                
                ),
                EmployeeInfoPlugin(
                    sources=["rio_people"],
                    available_nicknames=["Katya LAY","Ольга Воропаева","Алла","Камила","Ксения","М","Антон"],
                    available_chats=["Забота Рио🧡","Ы"],
                
                ),
                WelcomePlugin(
                    base_template=RIO_WELCOME_TEMPLATE,
                    questions=RIO_WELCOME_QUESTIONS,
                    n_questions=3,
                ),

                
            ],
            services=[
                PeopleDirectoryService(
                    sources={
                        "rio_people_birthdays": {
                            "name": "rio_people_birthdays",
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "birthday": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people_work": {
                            "name": "rio_people_work",
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "start_date": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people": {
                            "url": "https://docs.google.com/spreadsheets/d/11xOQjQxoYvfbyOAu5oPtR0SE6xkgCFJY7Q0_Zt1ShuY/export?format=csv",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode": "named",
                            "required_fields": ("fio",),
                            "fields_mapping": {

                                # база
                                "fio": "ФИО",
                                "status": "Статус",
                                "position": "Должность",

                                # занятость / hr
                                "employment_type": "формат трудоустройства",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                # даты
                                "start_date": "дата выхода",
                                "birthday": "день рождения",
                                "probation_end": "окончание ИС",

                                # тепловые / встречи (исправлены названия)
                                "last_heat": "Дата посл  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",

                                "last_1to1": "Дата посл 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",

                                # hr данные
                                "employee_card": "Карточка сотрдуника",

                                # человек
                                "gender": "пол",
                                "stack": "Специализация",

                                # орг структура
                                "manager": "Руководитель",
                                "project": "Точка",  # тут спорно, но лучше чем терять поле

                                # контакты
                                "phone": "Телефон",
                                "telegram_contact": "Телеграм",

                                # доп
                                "children": "дети",
                                "address": "адрес проживания",

                                # медиа
                                "photo_url": "фото для поздравления",
                            }
                        },
                        
                    },
                    cache_ttl=300,
                )
            ],
            actions=[
                Action(name="birthday_test", func_name="birthday_test", scope="private", type=ActionType.COMMAND),
                Action(name="birthday_chat_status", func_name="birthday_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="user_join", func_name="handle_chat_member_join", scope="private", type=ActionType.CHAT_MEMBER_JOIN),
                Action(name="register_birthday_chat", func_name="birthday_register_chat", scope="private", type=ActionType.COMMAND),
                Action(name="work_test", func_name="work_test", scope="private", type=ActionType.COMMAND),
                Action(name="work_chat_status", func_name="work_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="register_work_chat", func_name="work_register_chat", scope="private", type=ActionType.COMMAND),
            ],
        )


        await rio_bot_instance.init_plugins()
        await rio_max_bot_instance.init_plugins()
        # await threeit_bot_instance.init_plugins()
        #
        await keepcat_bot_instance.init_plugins()
        await clera_bot_instance.init_plugins()
        await not_shma_bot_instance.init_plugins()

        tasks = [
            asyncio.create_task(rio_bot_instance.run()),
            # asyncio.create_task(threeit_bot_instance.run()),
            asyncio.create_task(keepcat_bot_instance.run()),
            asyncio.create_task(clera_bot_instance.run()),
            asyncio.create_task(not_shma_bot_instance.run()),
            asyncio.create_task(rio_max_bot_instance.run()),
            
        ]

        try:
            await asyncio.gather(*tasks)
        except (asyncio.CancelledError, KeyboardInterrupt):
            logging.info("Shutting down gracefully...")

            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

            await rio_bot_instance.shutdown()
            # await threeit_bot_instance.shutdown()
            await keepcat_bot_instance.shutdown()
            await clera_bot_instance.shutdown()
            await not_shma_bot_instance.shutdown()
            await rio_max_bot_instance.shutdown()

    else:
        logging.info("Running in testing mode.")

        max_test_bot_instance = MaxBotInstance(
            token=os.getenv("MAX_TEST_BOT_TOKEN", ""),
            api_key=os.getenv("MAX_TEST_API_KEY",""),
            name="MaxTestBot",
            plugins=[
                BirthdayPlugin(
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/testing/birthdayMax",
                    people_source="rio_people_birthdays",
                    hour=7,
                    minute=0,
                    chat_id="-73548766634171",
                ),
                WorkExperiencePlugin(
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/testing/workMax",
                    people_source="rio_people_work",
                    hour=7,
                    minute=0,
                    chat_id="-73548766634171",
                ),
                EmployeeInfoPlugin(
                    sources=["rio_people"],
                    available_nicknames=["silvercat86","katyalay7","виктор"],
                    available_chats=[""],
                ),
                WelcomePlugin(
                    base_template=RIO_WELCOME_TEMPLATE,
                    questions=RIO_WELCOME_QUESTIONS,
                    
                ),
            ],
            services=[
                PeopleDirectoryService(
                    sources={
                       
                        "rio_people_birthdays": {
                            "name": "rio_people_birthdays",
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),

                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "birthday": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people_work": {
                            "name": "rio_people_work",
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "start_date": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people": {
                            "url": "https://docs.google.com/spreadsheets/d/11xOQjQxoYvfbyOAu5oPtR0SE6xkgCFJY7Q0_Zt1ShuY/export?format=csv",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode": "named",
                            "required_fields": ("fio",),
                            "fields_mapping": {

                                # база
                                "fio": "ФИО",
                                "status": "Статус",
                                "position": "Должность",

                                # занятость / hr
                                "employment_type": "формат трудоустройства",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                # даты
                                "start_date": "дата выхода",
                                "birthday": "день рождения",
                                "probation_end": "окончание ИС",

                                # тепловые / встречи (исправлены названия)
                                "last_heat": "Дата посл  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",

                                "last_1to1": "Дата посл 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",

                                # hr данные
                                "employee_card": "Карточка сотрдуника",

                                # человек
                                "gender": "пол",
                                "stack": "Специализация",

                                # орг структура
                                "manager": "Руководитель",
                                "project": "Точка",  # тут спорно, но лучше чем терять поле

                                # контакты
                                "phone": "Телефон",
                                "telegram_contact": "Телеграм",

                                # доп
                                "children": "дети",
                                "address": "адрес проживания",

                                # медиа
                                "photo_url": "фото для поздравления",
                            }
                        },
                        
                        
                    },
                    cache_ttl=300,
                )
            ],
            actions=[
                Action(name="birthday_test", func_name="birthday_test", scope="private", type=ActionType.COMMAND),
                Action(name="birthday_chat_status", func_name="birthday_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="user_join", func_name="handle_chat_member_join", scope="private", type=ActionType.CHAT_MEMBER_JOIN),
            ]

        )

        test_bot_instance = TelegramBotInstance(
            token=os.getenv("TEST_BOT_TOKEN", ""),
            api_key=os.getenv("TEST_API_KEY",""),
            name="TestBot",
            plugins=[
                # CleverShmaPlugin(),
                ComplimentPlugin(),
                BirthdayPlugin(
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/testing/birthday",
                    people_source="rio_people_birthdays",
                    hour=7,
                    minute=0,
                    chat_id="-4898624653",
                    
                ),
                WorkExperiencePlugin(
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/testing/work",
                    people_source="rio_people_work",
                    hour=7,
                    minute=0,
                    chat_id="-4898624653",

                
                ),

                WelcomePlugin(
                    base_template=RIO_WELCOME_TEMPLATE,
                    questions=RIO_WELCOME_QUESTIONS,
                    n_questions=3,
                    ),

                StartPlugin(
                    messages=RIO_START_TEMPLATES
                ),
                MemePlugin(),
                March8Plugin(
                    template=THREEIT_MARCH8_TEMPLATE,
                    storage_dir="data/testing/march8",
                    hour=0,
                    minute=0,
                    photo = "data/testing/march8/image.png"
                ),
                EmployeeInfoPlugin(
                    sources=["clera_people"],
                    available_nicknames=["silvercat86","katyalay7"],
                    available_chats=["test"],
                    scope_chats=[-4898624653]
                    
                
                ),
                ],
            services=[
                PeopleDirectoryService(
                    sources={
                       
                        "rio_people_birthdays": {
                            "name": "rio_people_birthdays",
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "birthday": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people_work": {
                            "name": "rio_people_work",
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "start_date": 2,
                                "photo_url": 3
                        }
                        },
                        "rio_people": {
                            "url": "https://docs.google.com/spreadsheets/d/11xOQjQxoYvfbyOAu5oPtR0SE6xkgCFJY7Q0_Zt1ShuY/export?format=csv",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode": "named",
                            "required_fields": ("fio",),
                            "fields_mapping": {

                                # база
                                "fio": "ФИО",
                                "status": "Статус",
                                "position": "Должность",

                                # занятость / hr
                                "employment_type": "формат трудоустройства",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                # даты
                                "start_date": "дата выхода",
                                "birthday": "день рождения",
                                "probation_end": "окончание ИС",

                                # тепловые / встречи (исправлены названия)
                                "last_heat": "Дата посл  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",

                                "last_1to1": "Дата посл 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",

                                # hr данные
                                "employee_card": "Карточка сотрдуника",

                                # человек
                                "gender": "пол",
                                "stack": "Специализация",

                                # орг структура
                                "manager": "Руководитель",
                                "project": "Точка",  # тут спорно, но лучше чем терять поле

                                # контакты
                                "phone": "Телефон",
                                "telegram_contact": "Телеграм",

                                # доп
                                "children": "дети",
                                "address": "адрес проживания",

                                # медиа
                                "photo_url": "фото для поздравления",
                            }
                        },
                        "clera_people": {
                            "name": "clera_people",
                            "url": "https://docs.google.com/spreadsheets/d/12DHRyjO2tyd90NPlFr1GKKe80hww-pwWMl3eaqEWYPM/export?format=csv&gid=1875323650",
                            "mode": "named",
                            "required_fields": ("fio",),
                            "fields_mapping": {

                                "fio": "ФИО",
                                "status": "Статус",
                                "position": "Должность",

                                "employment": "Занятость",
                                "employment_type": "формат трудоустройства",
                                "engagement": "Вовлеченность",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                "start_date": "дата выхода",
                                "current_date": "текущая дата",
                                "probation_end": "окончание ИС",
                                "birthday": "День рождения",

                                "resume": "Резюме",
                                "offer": "Оффер",
                                "employee_card": "Карточка сотрудника",

                                "last_heat": "Дата последней  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",
                                "last_1to1": "Дата 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",
                                "one_to_one_notes": "1 to 1",

                                "gender": "пол",
                                "stack": "Стэк",

                                "phone": "Телефон",
                                "username": "контакт ТГ",
                                "telegram_contact": "контакт ТГ",
                                "email": "почта",
                                "emergency_contact": "контакт эккстреснгой свзяи",

                                "welcome_training": "Вэлком тренинг",
                                "salary": "Зарплата-ставка",
                                "social_package": "доступный соц пакет",
                                "salary_changes": "изменения по зп",

                                "children": "дети",
                                "address": "адрес проживания",

                                "extra_comments": "Комментарии",
                            }
                        },


                    },
                    cache_ttl=300,
                )
            ],
            actions=[
                Action(name="birthday_test", func_name="birthday_test", scope="private", type=ActionType.COMMAND),
                Action(name="birthday_chat_status", func_name="birthday_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="user_join", func_name="handle_chat_member_join", scope="private", type=ActionType.CHAT_MEMBER_JOIN),
                Action(name="register_birthday_chat", func_name="birthday_register_chat", scope="private", type=ActionType.COMMAND),
                Action(name="work_test", func_name="work_test", scope="private", type=ActionType.COMMAND),
                Action(name="work_chat_status", func_name="work_chat_status", scope="private", type=ActionType.COMMAND),
                Action(name="register_work_chat", func_name="work_register_chat", scope="private", type=ActionType.COMMAND),
            ],


        )
        await test_bot_instance.init_plugins()
        await max_test_bot_instance.init_plugins()

        tasks = [
            asyncio.create_task(test_bot_instance.run()), 
            asyncio.create_task(max_test_bot_instance.run()),
        ]

        try:
            await asyncio.gather(*tasks)
        except (asyncio.CancelledError, KeyboardInterrupt):
            logging.info("Shutting down gracefully...")

            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

            await test_bot_instance.shutdown()
            await max_test_bot_instance.shutdown()
            

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by user.")