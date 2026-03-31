"""
Django settings for bot_platform project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-dev-secret")

if SECRET_KEY == "unsafe-dev-secret":
    print("WARNING: Using unsafe development secret key!")

DEBUG = os.getenv("DEBUG", "0") == "1"

BOT_API_KEY = os.getenv("BOT_API_KEY")



ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",") if not DEBUG else ["*"]


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    "https://keepcat.ru",
    "https://www.keepcat.ru",
    "http://localhost:8080",
]

PEOPLE_SOURCES = {
    "rio_people": {
        "name": "rio_people",
        "service_account_b64": os.getenv("RIO_CREDENTIALS_BASE64", ""),
        "mode": "named",
        "url": "https://docs.google.com/spreadsheets/d/1-5BsFz-i9jnAy-CP_1w7IeBt8IzRDCneaj-EbECADOs/export?format=csv&gid=1875323650",
        "fields_mapping": {
            "fio": "ФИО",
            "username": "Телеграм",
            "birthday": "день рождения",
            "start_date": "дата выхода",
        },
    },
}

# APPS

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    'accounts',
    'candidates',
    'communication',
    'companies',
    'events',
    'api',
]


# MIDDLEWARE

MIDDLEWARE = [
    "core.middleware.ApiKeyMiddleware",

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'bot_platform.urls'


# TEMPLATES

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'bot_platform.wsgi.application'


# DATABASE

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "bot_platform"),
        "USER": os.getenv("DB_USER", "bot_platform"),
        "PASSWORD": os.getenv("DB_PASSWORD", "bot_platform"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


# PASSWORD VALIDATION

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]


# INTERNATIONALIZATION

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Almaty")

USE_I18N = True
USE_TZ = True


# STATIC

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
}



# LOGGING

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
    "loggers": {
        "django.security.csrf": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}