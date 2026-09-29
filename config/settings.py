import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def validate_production_environment(env=None) -> list[str]:
    values = os.environ if env is None else env
    on_vercel = str(values.get("VERCEL", "")).lower() in {"1", "true"}
    debug = str(values.get("DJANGO_DEBUG", "false" if on_vercel else "true")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    production = on_vercel or not debug
    if not production:
        return []

    errors = []
    secret = values.get("DJANGO_SECRET_KEY", "")
    if (
        len(secret) < 50
        or secret.startswith("unsafe-development-key")
        or secret == "change-me-in-development"
    ):
        errors.append("DJANGO_SECRET_KEY deve ser um segredo forte com ao menos 50 caracteres.")
    database_url = values.get("DATABASE_URL", "")
    postgres_host = values.get("POSTGRES_HOST", "")
    if on_vercel and not database_url.startswith(("postgres://", "postgresql://")):
        errors.append("DATABASE_URL PostgreSQL persistente é obrigatório na Vercel.")
    elif not database_url.startswith(("postgres://", "postgresql://")):
        if not postgres_host:
            errors.append(
                "Configure DATABASE_URL PostgreSQL ou POSTGRES_HOST; SQLite não é permitido."
            )
        if not str(values.get("POSTGRES_USER", "")).strip():
            errors.append("POSTGRES_USER é obrigatório quando DATABASE_URL não é usado.")
        if not str(values.get("POSTGRES_PASSWORD", "")).strip():
            errors.append("POSTGRES_PASSWORD é obrigatório quando DATABASE_URL não é usado.")
    allowed_hosts = [
        host.strip() for host in values.get("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()
    ]
    if not allowed_hosts or "*" in allowed_hosts or ".vercel.app" in allowed_hosts:
        errors.append("DJANGO_ALLOWED_HOSTS deve listar hosts concretos, sem curinga global.")
    origins = [
        origin.strip()
        for origin in values.get("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if not origins or any(
        not origin.lower().startswith("https://")
        or "localhost" in origin
        or "127.0.0.1" in origin
        or "*" in origin
        for origin in origins
    ):
        errors.append("CORS_ALLOWED_ORIGINS deve listar origens HTTPS concretas do frontend.")
    csrf_origins = [
        origin.strip()
        for origin in values.get("CSRF_TRUSTED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if not csrf_origins or any(
        not origin.lower().startswith("https://") or "localhost" in origin or "*" in origin
        for origin in csrf_origins
    ):
        errors.append("CSRF_TRUSTED_ORIGINS deve listar origens HTTPS concretas.")
    if on_vercel and debug:
        errors.append("DJANGO_DEBUG deve ser false na Vercel.")
    return errors


PRODUCTION_ERRORS = validate_production_environment()
if PRODUCTION_ERRORS:
    raise ImproperlyConfigured(
        "Configuração insegura para produção: " + " ".join(PRODUCTION_ERRORS)
    )

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "unsafe-development-key-for-local-testing-only-1234567890"
)
DEBUG = env_bool("DJANGO_DEBUG", default=not env_bool("VERCEL"))
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.inventory",
    "apps.orders",
    "apps.audit",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
        )
    }
elif POSTGRES_HOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "gestaobrindes"),
            "USER": os.getenv("POSTGRES_USER", ""),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": POSTGRES_HOST,
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    # SQLite keeps the project runnable before local PostgreSQL is provisioned.
    # Deployed environments must set POSTGRES_HOST.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Gestão Brindes API",
    "DESCRIPTION": "API modular para catálogo, estoque, solicitações e auditoria.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173" if DEBUG else "")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
