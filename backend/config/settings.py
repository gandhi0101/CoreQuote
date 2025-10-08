from pathlib import Path
import environ
import os

# --- Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Env
env = environ.Env(
    DEBUG=(bool, False),
)
# Carga backend/.env (ajusta si usas otra ruta)


# --- Core
SECRET_KEY = env("SECRET_KEY", default="dev-not-secure")
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [u.strip() for u in env("CSRF_TRUSTED_ORIGINS", default="http://localhost,http://127.0.0.1").split(",") if u.strip()]

# Railway expone el dominio público en una variable dedicada que agregamos
# dinámicamente para evitar configurarlo manualmente.
railway_public_domain = env("RAILWAY_PUBLIC_DOMAIN", default=None)
if railway_public_domain:
    ALLOWED_HOSTS.append(railway_public_domain)
    CSRF_TRUSTED_ORIGINS.append(f"https://{railway_public_domain}")


# --- Apps mínimas (agrega las tuyas aquí)
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # my locales
    "accounts",
    "clients",
    "inventory",
    "quotes",
    "reports",
]

# --- Middleware (WhiteNoise solo requiere estar en la lista)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# --- Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # crea la carpeta si la usarás
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Base de datos (Postgres por env / Railway DATABASE_URL)
default_db = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": env("POSTGRES_DB", default="corequote"),
    "USER": env("POSTGRES_USER", default="corequote"),
    "PASSWORD": env("POSTGRES_PASSWORD", default=""),
    "HOST": env("POSTGRES_HOST", default="db"),
    "PORT": env("POSTGRES_PORT", default="5432"),
}

database_url = env("DATABASE_URL", default=None)
if database_url:
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {"default": default_db}

# Railway recomienda mantener conexiones abiertas; se vuelve configurable.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# --- I18N / TZ
LANGUAGE_CODE = "es-mx"
LANGUAGES = [("es-mx", "Español (México)"), ("en", "English")]
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# --- Static
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise con hash/manifest solo en producción
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Otros
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
