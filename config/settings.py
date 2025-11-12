import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# Carregar .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# DJANGO CORE
# ==============================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-insegura")  # Segurança
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
<<<<<<< HEAD
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".onrender.com"]  # Seguro para ambiente local
=======
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend-lab-eng.onrender.com"]  # Seguro para ambiente local
>>>>>>> ca6e0cc8b708bec23b4bb84f57e7067d8ee97868

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

    # Terceiros
    "rest_framework",
    "corsheaders",

    # Seus Apps
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

# ======================================================
# BANCO DE DADOS – AUTOMÁTICO (SQLite para teste / MySQL para produção)
# ======================================================
USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQLDATABASE", ""),
            "USER": os.getenv("MYSQLUSER", ""),
            "PASSWORD": os.getenv("MYSQLPASSWORD", ""),
            "HOST": os.getenv("MYSQLHOST", ""),
            "PORT": os.getenv("MYSQLPORT", "3306"),
        }
    }

# ==============================
# CONFIGURAÇÕES GERAIS
# ==============================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# REST & JWT
# ==============================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "PAGE_SIZE": 10,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=3),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ==============================
# CORS (para frontend local)
# ==============================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://frontend-lab-eng.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True
