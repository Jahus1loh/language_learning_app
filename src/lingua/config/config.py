import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")


class Config:
    ROOT = Path(__file__).resolve().parents[1]

    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    DATA_DIR = ROOT / "data"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    WTF_CSRF_TIME_LIMIT = None

    DB_CONFIG = {
        "host": os.environ.get("DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("DB_PORT", 3306)),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "pythonlogin"),
        "autocommit": True,
    }

    PASSWORD_HASH_METHOD = "scrypt:32768:8:3"
