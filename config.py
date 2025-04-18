import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"

    DB_CONFIG: Dict[str, Any] = {
        "user": os.getenv("DB_USER", "launcher_user"),
        "password": os.getenv("DB_PASSWORD", ""),
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "launcher"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "ssl": True
    }

    ADMIN_ROLE_ID: int = int(os.getenv("ADMIN_ROLE_ID", 0))
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")

    @classmethod
    def validate(cls):
        errors = []
        if not cls.BOT_TOKEN:
            errors.append("Не задан BOT_TOKEN в .env")
        if not cls.DB_CONFIG["password"]:
            errors.append("Не задан пароль БД (DB_PASSWORD)")
        if cls.ADMIN_ROLE_ID == 0:
            errors.append("ADMIN_ROLE_ID не настроен")

        if errors:
            raise EnvironmentError("\n".join(errors))

Config.validate()