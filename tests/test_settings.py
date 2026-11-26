from backend.config.settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True
