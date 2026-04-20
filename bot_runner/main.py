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
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/rio/birthday",
                    people_source="rio_people_birthdays",
                    hour=9,
                    minute=0,
                    dry_run=False,
                    chat_file="data/rio/birthday/chats.txt",
                ),
                WorkExperiencePlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/rio/work",
                    people_source="rio_people_work",
                    hour=9,
                    minute=0,
                    dry_run=False,
                    chat_file="data/rio/birthday/chats.txt",
                
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
                    chat_file="data/rio/birthday/chats.txt",
                    storage_dir="data/rio/march8",
                    hour=9,
                    minute=0,
                    photo = "data/rio/march8/image.jpg"
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
                                "photo": 3
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
                                "photo": 3
                        }
                        },

                    },
                    cache_ttl=300,
                )
            ]
        )

        

        keepcat_bot_instance = TelegramBotInstance(
            token=os.getenv("KEEPCAT_BOT_TOKEN", ""),
            api_key=os.getenv("KEEPCAT_API_KEY",""),
            name="KeepCatBot",
            plugins=[
                EmployeeInfoPlugin(),
                StartPlugin(
                    messages=RIO_START_TEMPLATES
                ),
            ],
            services=[
                PeopleDirectoryService(
                    sources={
                        "threeit_people": {
                            "url": "https://docs.google.com/spreadsheets/d/1w3KMR_4cRlpG_qdsmdCOJ30ZCiAGtKItLmHHsLIYsqI/export?format=csv",
                            "mode": "named",
                            "required_fields": ("fio",),
                            "fields_mapping": {

                                "fio": "ФИО",
                                "status": "Статус",
                                "position": "Должность",
                                "workload": "Занятость",
                                "employment_type": "формат трудоустройства",
                                "format": "Форма",
                                "engagement": "Вовлеченность",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                "start_date": "дата выхода",
                                "current_date": "текущая дата",
                                "probation_end": "окончание ИС",

                                "resume": "Резюме",
                                "offer": "Оффер",
                                "employee_card": "Карточка сотрудника",

                                "last_heat": "Дата последней  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",

                                "last_1to1": "Дата 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",

                                "gender": "пол",
                                "stack": "Стэк",
                                "project": "Проект",
                                "project_description": "Описание проекта",

                                "manager": "Руководитель",

                                "phone": "Телефон",

                                "welcome_training": "Вэлком тренинг",

                                "salary": "Зарплата-ставка",
                                "social_package": "доступный соц пакет",
                                "salary_changes": "изменения по зп",

                                "children": "дети",
                                "address": "адрес проживания",

                                "telegram_contact": "контакт ТГ",
                                "username": "контакт ТГ",

                                "email": "почта",

                                "birthday": "День рождения",

                                "emergency_contact": "контакт эккстреснгой свзяи",
                        },},
                        "rio_people_birthdays": {
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "birthday": 2,
                                "photo": 3
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
                                "photo": 3
                        }
                        },},
                        
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
                ]
        )

        rio_max_bot_instance = MaxBotInstance(
            token=os.getenv("RIO_MAX_BOT_TOKEN", ""),
            api_key=os.getenv("RIO_MAX_API_KEY",""),
            name="RioMaxBot",
            plugins=[
                BirthdayPlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/rio/max/birthday",
                    people_source="rio_people_birthdays",
                    hour=9,
                    minute=0,
                    dry_run=False,
                    chat_id="-72336909860345",
                ),
                WorkExperiencePlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/rio/max/work",
                    people_source="rio_people_work",
                    hour=9,
                    minute=0,
                    dry_run=False,
                    chat_id="-72336909860345"
                
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
                    },
                    cache_ttl=300,
                )
            ]
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
                    csv_path="https://docs.google.com/spreadsheets/d/1EdBbNp8QLD04-TNl5uIYmk2NJaZCguyzTbGSnhp5ld4/export?format=csv&gid=0",
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/testing/birthdayMax",
                    people_source="rio_people_birthdays",
                    hour=7,
                    minute=0,
                    chat_id="-73548766634171",
                ),
                WorkExperiencePlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1EdBbNp8QLD04-TNl5uIYmk2NJaZCguyzTbGSnhp5ld4/export?format=csv&gid=1937147644",
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/testing/workMax",
                    people_source="rio_people_work",
                    hour=7,
                    minute=0,
                    chat_id="-73548766634171",
                ),
            ],
            services=[
                PeopleDirectoryService(
                    sources={
                       
                        "rio_people_birthdays": {
                            "name": "rio_people_birthdays",
                            "url": "https://docs.google.com/spreadsheets/d/1EdBbNp8QLD04-TNl5uIYmk2NJaZCguyzTbGSnhp5ld4/export?format=csv&gid=0",
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
                            "url": "https://docs.google.com/spreadsheets/d/1EdBbNp8QLD04-TNl5uIYmk2NJaZCguyzTbGSnhp5ld4/export?format=csv&gid=1937147644",
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "start_date": 2,
                                "photo_url": 3
                        }
                        },
                        
                        
                    },
                    cache_ttl=300,
                )
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
                    csv_path="https://docs.google.com/spreadsheets/d/1EdBbNp8QLD04-TNl5uIYmk2NJaZCguyzTbGSnhp5ld4/export?format=csv&gid=0",
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/testing/birthday",
                    people_source="rio_people_birthdays",
                    hour=7,
                    minute=0,
                    dry_run=False,
                    chat_file="data/testing/birthday/chat.txt",
                ),
                WorkExperiencePlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/testing/work",
                    people_source="rio_people_work",
                    hour=9,
                    minute=0,
                    dry_run=False,
                    chat_file="data/testing/birthday/chat.txt",
                
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
                    chat_file="data/testing/birthday/chat.txt",
                    storage_dir="data/testing/march8",
                    hour=0,
                    minute=0,
                    photo = "data/testing/march8/image.png"
                ),
                EmployeeInfoPlugin(
                    sources=["threeit_people","rio_people"],
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
                            "url": "https://docs.google.com/spreadsheets/d/1EdBbNp8QLD04-TNl5uIYmk2NJaZCguyzTbGSnhp5ld4/export?format=csv&gid=0",
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
                            "url": "https://docs.google.com/spreadsheets/d/1EdBbNp8QLD04-TNl5uIYmk2NJaZCguyzTbGSnhp5ld4/export?format=csv&gid=1937147644",
                            "mode": "indexed",
                            "required_fields": ("fio",),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "start_date": 2,
                                "photo_url": 3
                        }
                        },

                    },
                    cache_ttl=300,
                )
            ]
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