from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
import pymysql
pymysql.install_as_MySQLdb()
# Carrega o .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# DJANGO CORE
# ==============================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-insegura")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".onrender.com"]

# ==============================
# APPS
# ==============================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # terceiros
    "rest_framework",
    "corsheaders",

    # locais
    "api",
]

AUTH_USER_MODEL = "api.Usuario"

# ==============================
# MIDDLEWARE
# ==============================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
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
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ==============================
# BANCO DE DADOS (MySQL Railway)
# ==============================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQLDATABASE", "railway"),
        "USER": os.getenv("MYSQLUSER", "root"),
        "PASSWORD": os.getenv("MYSQLPASSWORD", ""),
        "HOST": os.getenv("MYSQLHOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQLPORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# ==============================
# CONFIG PADRÕES
# ==============================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# REST FRAMEWORK / JWT
# ==============================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
     "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,  # número de projetos por página
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=3),  # token dura 3 horas
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # refresh dura 1 dia
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ==============================
# CORS (para React local)
# ==============================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://frontend-jn.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True