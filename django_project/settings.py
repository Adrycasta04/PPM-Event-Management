"""Django settings for the event management project."""

import os
from pathlib import Path

from django.contrib.messages import constants as message_constants
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name):
    return [
        value.strip()
        for value in os.environ.get(name, "").split(",")
        if value.strip()
    ]


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(f"{name} must be an integer.") from exc


IS_RENDER = env_bool("RENDER")
DEBUG = env_bool("DJANGO_DEBUG", default=not IS_RENDER)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-development-only-change-me"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DEBUG is disabled."
        )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
if DEBUG:
    ALLOWED_HOSTS.extend(["localhost", "127.0.0.1", "[::1]"])
ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "events",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]
if not DEBUG:
    MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")
MIDDLEWARE += [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "django_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.roles",
            ],
        },
    },
]

WSGI_APPLICATION = "django_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "it-it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
if not DEBUG:
    STORAGES["staticfiles"]["BACKEND"] = (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )

MESSAGE_TAGS = {
    message_constants.ERROR: "danger",
}

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "events:home"
LOGOUT_REDIRECT_URL = "events:home"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", default=3600)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
