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



ALLOWED_HOSTS = ["*"]#os.getenv("ALLOWED_HOSTS", "").split(",") if not DEBUG else ["*"]


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    "https://keepcat.ru",
    "https://www.keepcat.ru",
]

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
]


# MIDDLEWARE

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # "whitenoise.middleware.WhiteNoiseMiddleware",
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



# CELERY

CELERY_BROKER_URL = "redis://redis:6379/0"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CELERY_TIMEZONE = os.getenv("TIME_ZONE", "Asia/Almaty")


# LOGGING

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "backend_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "backend.log",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "backend": {
            "handlers": ["backend_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}