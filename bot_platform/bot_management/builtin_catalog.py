def contract(fields):
    return {"fields": fields, "additional_fields": False}


STRING = {"type": "string"}
INTEGER = {"type": "integer"}
NUMBER = {"type": "number"}


SERVICE_DEFINITIONS = {
    "people_directory_service": {
        "title": "Справочник сотрудников",
        "description": "Загружает и кэширует сведения о сотрудниках из настроенных источников.",
        "default_config": {"sources": {}, "cache_ttl": 300},
        "config_schema": {
            "sources": {"type": "dict", "label": "Источники сотрудников"},
            "cache_ttl": {"type": "int", "label": "Время кэша, секунд", "min": 1},
        },
        "runtime_schema": contract({
            "cache_ttl": {**INTEGER, "required": False},
            "sources": {
                "type": "object",
                "additionalProperties": {"type": "object", "additionalProperties": True},
                "required": False,
            },
        }),
    },
}


PLUGIN_DEFINITIONS = {
    "birthday_plugin": {
        "title": "Поздравления с днём рождения",
        "description": "Отправляет поздравления сотрудникам по расписанию.",
        "default_config": {"templates": "", "storage_dir": "data/birthday", "people_source": "", "hour": 6, "minute": 0, "chat_id": ""},
        "config_schema": {
            "templates": {"type": "string", "label": "Код пакета шаблонов", "required": True},
            "storage_dir": {"type": "string", "label": "Каталог данных", "required": True},
            "people_source": {"type": "string", "label": "Источник сотрудников", "required": True},
            "hour": {"type": "int", "label": "Час отправки", "min": 0, "max": 23},
            "minute": {"type": "int", "label": "Минута отправки", "min": 0, "max": 59},
            "chat_id": {"type": "chat", "label": "Целевой чат", "required": True},
        },
        "runtime_schema": contract({
            "chat_id": {"anyOf": [STRING, INTEGER], "required": True},
            "hour": {**INTEGER, "minimum": 0, "maximum": 23, "required": False},
            "minute": {**INTEGER, "minimum": 0, "maximum": 59, "required": False},
            "people_source": {**STRING, "required": True}, "storage_dir": {**STRING, "required": True},
            "templates": {**STRING, "required": True},
        }),
        "required_services": ["people_directory_service"],
        "actions_schema": {
            "birthday_test": {"types": ["command"]}, "birthday_chat_status": {"types": ["command"]},
            "birthday_register_chat": {"types": ["command"]},
        },
    },
    "work_experience_plugin": {
        "title": "Годовщины работы", "description": "Поздравляет сотрудников с годовщиной работы.",
        "default_config": {"templates_by_years": {}, "storage_dir": "data/work_experience", "people_source": "", "hour": 6, "minute": 0, "chat_id": ""},
        "config_schema": {
            "templates_by_years": {"type": "dict", "label": "Шаблоны по количеству лет", "required": True},
            "storage_dir": {"type": "string", "label": "Каталог данных", "required": True},
            "people_source": {"type": "string", "label": "Источник сотрудников", "required": True},
            "hour": {"type": "int", "label": "Час отправки", "min": 0, "max": 23},
            "minute": {"type": "int", "label": "Минута отправки", "min": 0, "max": 59},
            "chat_id": {"type": "chat", "label": "Целевой чат", "required": True},
        },
        "runtime_schema": contract({
            "chat_id": {"anyOf": [STRING, INTEGER], "required": True},
            "hour": {**INTEGER, "minimum": 0, "maximum": 23, "required": False},
            "minute": {**INTEGER, "minimum": 0, "maximum": 59, "required": False},
            "people_source": {**STRING, "required": True}, "storage_dir": {**STRING, "required": True},
            "templates_by_years": {"type": "object", "additionalProperties": STRING, "required": True},
        }),
        "required_services": ["people_directory_service"],
        "actions_schema": {
            "work_test": {"types": ["command"]}, "work_chat_status": {"types": ["command"]},
            "work_register_chat": {"types": ["command"]},
        },
    },
    "march8_plugin": {
        "title": "Поздравление с 8 марта", "description": "Отправляет праздничное сообщение по расписанию.",
        "default_config": {"template": "С 8 марта!", "storage_dir": "data/march8", "photo": None, "hour": 6, "minute": 0, "chat_id": ""},
        "config_schema": {
            "template": {"type": "string", "label": "Текст поздравления", "format": "textarea", "required": True},
            "storage_dir": {"type": "string", "label": "Каталог данных", "required": True},
            "photo": {"type": "string", "label": "Путь к изображению"},
            "hour": {"type": "int", "label": "Час отправки", "min": 0, "max": 23},
            "minute": {"type": "int", "label": "Минута отправки", "min": 0, "max": 59},
            "chat_id": {"type": "chat", "label": "Целевой чат", "required": True},
        },
        "runtime_schema": contract({
            "chat_id": {"anyOf": [STRING, INTEGER], "required": True},
            "hour": {**INTEGER, "minimum": 0, "maximum": 23, "required": False},
            "minute": {**INTEGER, "minimum": 0, "maximum": 59, "required": False},
            "photo": {"anyOf": [STRING, {"type": "null"}], "required": False},
            "storage_dir": {**STRING, "required": True}, "template": {**STRING, "required": True},
        }),
        "required_services": [], "actions_schema": {},
    },
    "employee_info_plugin": {
        "title": "Информация о сотрудниках", "description": "Показывает разрешённую информацию из справочника сотрудников.",
        "default_config": {"sources": [], "available_nicknames": [], "available_chats": [], "scope_chats": []},
        "config_schema": {
            "sources": {"type": "list", "label": "Источники"}, "available_nicknames": {"type": "list", "label": "Разрешённые пользователи"},
            "available_chats": {"type": "list", "label": "Разрешённые чаты"}, "scope_chats": {"type": "list", "label": "Область чатов"},
        },
        "runtime_schema": contract({key: {"type": "array", "items": INTEGER if key == "scope_chats" else STRING, "required": False} for key in ("available_chats", "available_nicknames", "scope_chats", "sources")}),
        "required_services": ["people_directory_service"], "actions_schema": {},
    },
    "welcome_plugin": {
        "title": "Приветствие новых участников", "description": "Приветствует новых участников чата.",
        "default_config": {"base_template": "", "questions": [], "n_questions": 3, "dedupe_ttl_seconds": 30},
        "config_schema": {
            "base_template": {"type": "string", "label": "Шаблон приветствия", "format": "textarea"},
            "questions": {"type": "list", "label": "Вопросы"}, "n_questions": {"type": "int", "label": "Количество вопросов", "min": 0},
            "dedupe_ttl_seconds": {"type": "int", "label": "Защита от повторов, секунд", "min": 0},
        },
        "runtime_schema": contract({
            "base_template": {**STRING, "required": False}, "dedupe_ttl_seconds": {**INTEGER, "minimum": 0, "required": False},
            "n_questions": {**INTEGER, "minimum": 0, "required": False}, "questions": {"type": "array", "items": STRING, "required": False},
        }),
        "required_services": [], "actions_schema": {"handle_chat_member_join": {"types": ["chat_member_join"]}},
    },
    "start_plugin": {
        "title": "Команда Start", "description": "Отвечает на стартовую команду.",
        "default_config": {"messages": []}, "config_schema": {"messages": {"type": "list", "label": "Сообщения"}},
        "runtime_schema": contract({"messages": {"type": "array", "items": STRING, "required": False}}),
        "required_services": [], "actions_schema": {"start": {"types": ["command"]}},
    },
    "compliment_plugin": {
        "title": "Комплименты", "description": "Отправляет случайный комплимент.",
        "default_config": {"messages": []}, "config_schema": {"messages": {"type": "list", "label": "Комплименты"}},
        "runtime_schema": contract({"messages": {"type": "array", "items": STRING, "required": False}}),
        "required_services": [], "actions_schema": {"compliment": {"types": ["command"]}},
    },
    "meme_plugin": {
        "title": "Мемы", "description": "Работает с каталогом мемов.",
        "default_config": {"data_file": "data/memes/memes.txt"},
        "config_schema": {"data_file": {"type": "string", "label": "Файл с мемами"}},
        "runtime_schema": contract({"data_file": {**STRING, "required": False}}),
        "required_services": [], "actions_schema": {},
    },
    "clever_shma_plugin": {
        "title": "AI-ассистент", "description": "Генерирует ответы через OpenRouter-совместимый API.",
        "default_config": {"api_url": "https://openrouter.ai/api/v1/chat/completions", "model": "deepseek/deepseek-chat", "system_prompt": None, "temperature": 0.7, "max_tokens": 1024, "timeout_seconds": 60},
        "config_schema": {
            "api_url": {"type": "string", "label": "API URL"}, "model": {"type": "string", "label": "Модель"},
            "system_prompt": {"type": "string", "label": "Системный промпт", "format": "textarea"},
            "temperature": {"type": "float", "label": "Температура", "min": 0, "max": 2},
            "max_tokens": {"type": "int", "label": "Максимум токенов", "min": 1},
            "timeout_seconds": {"type": "float", "label": "Таймаут, секунд", "min": 0.1},
        },
        "runtime_schema": contract({
            "api_url": {**STRING, "required": False}, "max_tokens": {**INTEGER, "required": False}, "model": {**STRING, "required": False},
            "system_prompt": {"anyOf": [STRING, {"type": "null"}], "required": False},
            "temperature": {**NUMBER, "minimum": 0, "maximum": 2, "required": False}, "timeout_seconds": {**NUMBER, "required": False},
        }),
        "required_services": [], "actions_schema": {},
    },
}
