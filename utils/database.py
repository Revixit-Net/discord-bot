import mariadb
from config import Config
import logging

logger = logging.getLogger("discord_bot")

class DatabaseManager:
    def __init__(self):
        self.config = Config.DB_CONFIG
        self.conn = None

    def __enter__(self):
        self.connect()
        return self.conn.cursor()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def connect(self):
        try:
            self.conn = mariadb.connect(**self.config)
            self.conn.autocommit = False
        except mariadb.Error as e:
            logger.error(f"Ошибка подключения к БД: {str(e)}")
            raise

    def add_user(self, user_data: tuple):
        try:
            with self as cursor:
                cursor.execute(
                    """INSERT INTO users 
                    (username, password, accessToken, uuid, discord_id, serverID) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    user_data
                )
                logger.debug(f"Добавлен пользователь: {user_data[0]}")
                return True
        except mariadb.IntegrityError as e:
            logger.warning(f"Конфликт данных: {str(e)}")
            raise

    def delete_user(self, username: str):
        try:
            with self as cursor:
                # Удаление из связанных таблиц
                cursor.execute(
                    """DELETE users, hwid, auth 
                    FROM users 
                    LEFT JOIN hwid ON users.uuid = hwid.uuid 
                    LEFT JOIN auth ON users.uuid = auth.uuid 
                    WHERE users.username = ?""",
                    (username,)
                )
                logger.warning(f"Удален пользователь: {username}")
                return cursor.rowcount
        except mariadb.Error as e:
            logger.error(f"Ошибка удаления: {str(e)}")
            raise

    def check_existing_user(self, discord_id: int, username: str):
        try:
            with self as cursor:
                cursor.execute(
                    """SELECT uuid FROM users 
                    WHERE discord_id = ? OR username = ?""",
                    (discord_id, username)
                )
                return cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"Ошибка проверки пользователя: {str(e)}")
            raise

    def get_user_info(self, username: str):
        try:
            with self as cursor:
                cursor.execute(
                    """SELECT uuid, discord_id, serverID 
                    FROM users 
                    WHERE username = ?""",
                    (username,)
                )
                return cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"Ошибка получения данных: {str(e)}")
            raise

    def update_password(self, username: str, new_password: str):
        try:
            with self as cursor:
                cursor.execute(
                    """UPDATE users 
                    SET password = ? 
                    WHERE username = ?""",
                    (new_password, username)
                )
                logger.info(f"Обновлен пароль для: {username}")
                return cursor.rowcount
        except mariadb.Error as e:
            logger.error(f"Ошибка обновления пароля: {str(e)}")
            raise

    def get_all_users(self):
        try:
            with self as cursor:
                cursor.execute("SELECT username, discord_id FROM users")
                return cursor.fetchall()
        except mariadb.Error as e:
            logger.error(f"Ошибка получения списка: {str(e)}")
            raise