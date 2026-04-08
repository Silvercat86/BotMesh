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


from core.bot_instance import BotInstance

from plugins.compliment.plugin import ComplimentPlugin
from plugins.birthday.plugin import BirthdayPlugin
from plugins.work_experience.plugin import WorkExperiencePlugin
from plugins.welcome.plugin import WelcomePlugin
from plugins.start.plugin import StartPlugin
from plugins.memes.plugin import MemePlugin
from plugins.march8.plugin import March8Plugin
from plugins.employee_info.plugin import EmployeeInfoPlugin

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

        rio_bot_instance = BotInstance(
            token=os.getenv("RIO_BOT_TOKEN", ""),
            api_key=os.getenv("RIO_API_KEY",""),
            name="RioBot",
            plugins=[
                ComplimentPlugin(),
                BirthdayPlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/rio/birthday",
                    hour=9,
                    minute=0,
                    dry_run=False,
                    chat_file="data/rio/birthday/chats.txt",
                ),
                WorkExperiencePlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/rio/work",
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
                        "birthdays": {
                            "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                            "mode": "indexed",
                            "required_fields": ("fio", "birthday"),
                            "fields_mapping": {
                                "fio": 0,
                                "username": 1,
                                "birthday": 2,
                                "photo": 3
                            },
                        },
                        "rio_people": {
                            "name": "rio_people",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode" : "named",
                            "url": "https://docs.google.com/spreadsheets/d/11xOQjQxoYvfbyOAu5oPtR0SE6xkgCFJY7Q0_Zt1ShuY/export?format=csv&gid=1875323650",
                            "fields_mapping": {

                                "fio": "ФИО",
                                "birthday":"день рождения",
                                "status": "Статус",

                                "position": "Должность",
                                "stack": "Специализация",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                "start_date": "дата выхода",
                                "probation_end": "окончание ИС",

                                "employee_card": "Карточка сотрдуника",

                                "last_heat": "Дата посл  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",

                                "last_1to1": "Дата посл 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",

                                "gender": "пол",

                                "manager": "Руководитель",

                                "phone": "Телефон",
                                "telegram_contact": "Телеграм",

                                "employment_type": "формат трудоустройства",

                                "children": "дети",
                                "address": "Точка",

                            },
                        },
                        

                    },
                    cache_ttl=300,
                )
            ]
        )

        # threeit_bot_instance = BotInstance(
        #     token=os.getenv("THREEIT_BOT_TOKEN", ""),
        #     api_key=os.getenv("THREEIT_API_KEY",""),

        #     name="ThreeITBot",
        #     plugins=[
        #         ComplimentPlugin(),
        #         BirthdayPlugin(
        #             csv_path="https://docs.google.com/spreadsheets/d/1w3KMR_4cRlpG_qdsmdCOJ30ZCiAGtKItLmHHsLIYsqI/export?format=csv&gid=1875323650",
        #             templates=THREEIT_BIRTHDAY_TEMPLATES,
        #             storage_dir="data/TreeIT/birthday",
        #             hour=9,
        #             minute=0,
        #             dry_run=False,
        #             chat_file="data/TreeIT/birthday/chats.txt",
        #         ),
        #         WorkExperiencePlugin(
        #             csv_path="https://docs.google.com/spreadsheets/d/1ixGBmwFlGxpo4Q-vhyrct79hkDWBtM2ZOGhQVIfk3EM/export?format=csv&gid=1875323650",
        #             templates_by_years=THREEIT_WORK_TEMPLATES,
        #             storage_dir="data/TreeIT/work",
        #             hour=9,
        #             minute=0,
        #             dry_run=False,
        #             chat_file="data/TreeIT/birthday/chats.txt",
        #             column_map={
        #                 "fio": "фио",
        #                 "username": "контакт тг",
        #                 "start_date": "дата выхода",
        #                 "photo": "Фото"
        #             },
        #         ),
        #         WelcomePlugin(
        #             base_template=THREEIT_WELCOME_TEMPLATE,
        #             questions=THREEIT_WELCOME_QUESTIONS,
        #             n_questions=3,

        #         ),
        #         StartPlugin(
        #             messages=THREEIT_START_TEMPLATES
        #         ),
        #         MemePlugin(),
        #         March8Plugin(
        #             template=THREEIT_MARCH8_TEMPLATE,
        #             chat_file="data/TreeIT/birthday/chats.txt",
        #             storage_dir="data/TreeIT/march8",
        #             hour=9,
        #             minute=0,
        #             photo = "data/TreeIT/march8/image.jpg"
        #         ),
        #     ],
        #     services=[
        #         PeopleDirectoryService(
        #             sources={
        #                 "birthdays": {
        #                     "url": "https://docs.google.com/spreadsheets/d/1w3KMR_4cRlpG_qdsmdCOJ30ZCiAGtKItLmHHsLIYsqI/export?format=csv&gid=0",
        #                     "mode": "indexed",
        #                     "required_fields": ("fio", "birthday"),
        #                     "fields_mapping": {
        #                         "fio": 0,
        #                         "username": 1,
        #                         "birthday": 2,
        #                         "photo": 3
        #                     },
        #                 },
                        

        #             },
        #             cache_ttl=300,
        #         )
        #     ]
            
        # )

        keepcat_bot_instance = BotInstance(
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
        clera_bot_instance = BotInstance(
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


        await rio_bot_instance.init_plugins()
        # await threeit_bot_instance.init_plugins()
        await keepcat_bot_instance.init_plugins()
        await clera_bot_instance.init_plugins()

        tasks = [
            asyncio.create_task(rio_bot_instance.run()),
            # asyncio.create_task(threeit_bot_instance.run()),
            asyncio.create_task(keepcat_bot_instance.run()),
            asyncio.create_task(clera_bot_instance.run()),
            
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

    else:
        logging.info("Running in testing mode.")

        test_bot_instance = BotInstance(
            token=os.getenv("TEST_BOT_TOKEN", ""),
            api_key=os.getenv("TEST_API_KEY",""),
            name="TestBot",
            plugins=[
                ComplimentPlugin(),
                BirthdayPlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                    templates=RIO_BIRTHDAY_TEMPLATES,
                    storage_dir="data/testing/birthday",
                    hour=9,
                    minute=0,
                    dry_run=False,
                    chat_file="data/testing/birthday/chat.txt",
                ),
                WorkExperiencePlugin(
                    csv_path="https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                    templates_by_years=RIO_WORK_TEMPLATES,
                    storage_dir="data/testing/work",
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
                       
                        "threeit_people": {
                            "name": "threeit_people",
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
                            },
                        },
                        # "rio_people_birthdays": {
                        #     "name": "rio_people_birthdays",
                        #     "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=0",
                        #     "mode": "indexed",
                        #     "required_fields": ("fio",),
                        #     "fields_mapping": {
                        #         "fio": 0,
                        #         "username": 1,
                        #         "birthday": 2,
                        #         "photo_url": 3
                        # }
                        # },
                        # "rio_people_work": {
                        #     "name": "rio_people_work",
                        #     "url": "https://docs.google.com/spreadsheets/d/1QFdn6iAmc-krAIY75nDvWvn54LZrpjX5TfufZb1sJRg/export?format=csv&gid=1937147644",
                        #     "mode": "indexed",
                        #     "required_fields": ("fio",),
                        #     "fields_mapping": {
                        #         "fio": 0,
                        #         "username": 1,
                        #         "start_date": 2,
                        #         "photo_url": 3
                        # }
                        # },
                        # "rio_people": {
                        #     "name": "rio_people",
                        #     "type" : "mixed",
                        #     "sources": ["rio_people_birthdays", "rio_people_work"],
                        #     "key_field": "username",
                        #     "field_mapping": {
                        #         "fio" : "rio_people_birthdays",
                        #         "username" : "rio_people_birthdays",
                        #         "birthday" : "rio_people_birthdays",
                        #         "photo_url" : "rio_people_birthdays",
                        #         "start_date" : "rio_people_work",
                        #     }
                        # },
                        "rio_people": {
                            "name": "rio_people",
                            "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
                            "mode" : "named",
                            "url": "https://docs.google.com/spreadsheets/d/11xOQjQxoYvfbyOAu5oPtR0SE6xkgCFJY7Q0_Zt1ShuY/export?format=csv&gid=1875323650",
                            "fields_mapping": {

                                "fio": "ФИО",
                                "status": "Статус",

                                "position": "Должность",
                                "stack": "Специализация",
                                "zone": "Зона",
                                "risk": "Риск ухода",
                                "comments": "комментарии",

                                "start_date": "дата выхода",
                                "probation_end": "окончание ИС",

                                "employee_card": "Карточка сотрдуника",

                                "last_heat": "Дата посл  тепловой с Заботой",
                                "next_heat": "Дата след тепловой",

                                "last_1to1": "Дата посл 1 to 1 с рук",
                                "next_1to1": "Дата след 1 to 1 с рук",

                                "gender": "пол",

                                "manager": "Руководитель",

                                "phone": "Телефон",

                                "employment_type": "формат трудоустройства",

                                "children": "дети",
                                "address": "Точка",

                            },
                        },

                    },
                    cache_ttl=300,
                )
            ]
        )
        await test_bot_instance.init_plugins()

        tasks = [
            asyncio.create_task(test_bot_instance.run()), 
        ]

        try:
            await asyncio.gather(*tasks)
        except (asyncio.CancelledError, KeyboardInterrupt):
            logging.info("Shutting down gracefully...")

            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

            await test_bot_instance.shutdown()
            

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by user.")