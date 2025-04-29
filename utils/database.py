import mariadb
import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger("discord_bot")

class DatabaseManager:
    def __init__(self):
        self.config = Config.DB_CONFIG  # Конфигурация из config.py

    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для работы с курсором БД."""
        conn = None
        try:
            conn = mariadb.connect(**self.config)
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except mariadb.Error as e:
            logger.error(f"Ошибка БД: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def add_user(self, user_data: tuple) -> None:
        """Добавление пользователя в БД."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """INSERT INTO users 
                (username, password, uuid, discord_id, serverID) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                user_data
            )

    def delete_user(self, username: str) -> int:
        """Удаление пользователя из БД."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM users WHERE username = ?", 
                (username,)
            )
            return cursor.rowcount

    def check_existing_user(self, discord_id: int, username: str) -> bool:
        """Проверка существования пользователя."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT username FROM users WHERE discord_id = ? OR username = ?",
                (discord_id, username)
            )
            return cursor.fetchone() is not None

    def update_password(self, username: str, new_password: str) -> bool:
        """Обновление пароля пользователя."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (new_password, username)
            )
            return cursor.rowcount > 0

    def search_logins(self, query: str) -> list[str]:
        """Поиск логинов по частичному совпадению."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT username FROM users WHERE username LIKE ? LIMIT 10",
                (f"%{query}%",)
            )
            return [row[0] for row in cursor.fetchall()]

    def get_user_password(self, username: str) -> str | None:
        """Получение хеша пароля пользователя."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT password FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_user_info(self, username: str) -> tuple | None:
        """Получение информации о пользователе."""
        with self.get_cursor() as cursor:
            cursor.execute(
                """SELECT uuid, discord_id, serverID 
                FROM users 
                WHERE username = ?""",
                (username,)
            )
            return cursor.fetchone()

    def is_connected(self) -> bool:
        """Проверка подключения к БД."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
