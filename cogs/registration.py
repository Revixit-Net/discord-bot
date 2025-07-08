import discord
from discord.ext import commands
from discord import app_commands
import uuid
import logging
from utils.database import DatabaseManager
from utils.helpers import (
    hash_password,
    validate_username,
    validate_password,
    generate_error_code,
    verify_password
)
from config import Config

logger = logging.getLogger("discord_bot")

access_token = str(uuid.uuid4())

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()

    async def get_user_data(self, discord_id: int) -> tuple | None:
        """Получение данных пользователя по Discord ID"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT username, password FROM users WHERE discord_id = ?",
                (discord_id,)
            )
            return cursor.fetchone()

    @app_commands.command(
        name="reg",
        description="Регистрация игрового аккаунта"
    )
    @app_commands.describe(
        login="Логин (3-16 символов, a-Z, 0-9, _)",
        password="Пароль (минимум 8 символов)"
    )
    async def register(
        self,
        interaction: discord.Interaction,
        login: str,
        password: str
    ):
        """Обработчик команды /reg"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Валидация логина
            if error := validate_username(login):
                return await interaction.followup.send(f"❌ {error}", ephemeral=True)

            # Валидация пароля
            if error := validate_password(password):
                return await interaction.followup.send(f"❌ {error}", ephemeral=True)

            # Проверка существующего пользователя
            existing = self.db.check_existing_user(interaction.user.id, login)
            if existing:
                return await interaction.followup.send(
                    "❌ Логин уже занят или аккаунт привязан к вам!",
                    ephemeral=True
                )

            # Генерация данных
            user_data = (
                login,
                hash_password(password),
                interaction.user.id,
                "default",
                access_token
            )

            # Сохранение в БД
            self.db.add_user(user_data)
            
            await interaction.followup.send(
                "✅ Регистрация успешна! Используйте логин и пароль в лаунчере.",
                ephemeral=True
            )
            logger.info(f"Зарегистрирован новый аккаунт: {login}")

        except Exception as e:
            error_code = generate_error_code()
            logger.error(f"Ошибка регистрации ({error_code}): {str(e)}", exc_info=True)
            await interaction.followup.send(
                f"🚨 Ошибка {error_code}: Не удалось завершить регистрацию",
                ephemeral=True
            )

    @app_commands.command(
        name="changepassword",
        description="Сменить пароль"
    )
    @app_commands.describe(
        old_password="Текущий пароль",
        new_password="Новый пароль (мин. 8 символов)"
    )
    async def change_password(
        self,
        interaction: discord.Interaction,
        old_password: str,
        new_password: str
    ):
        """Смена пароля пользователем"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Получение данных пользователя
            user_data = await self.get_user_data(interaction.user.id)
            if not user_data:
                return await interaction.followup.send("❌ Аккаунт не найден!", ephemeral=True)

            # Проверка старого пароля
            current_hash = user_data[1]
            if not verify_password(old_password, current_hash):
                return await interaction.followup.send("❌ Неверный текущий пароль!", ephemeral=True)

            # Валидация нового пароля
            if error := validate_password(new_password):
                return await interaction.followup.send(f"❌ {error}", ephemeral=True)

            # Обновление пароля
            new_hash = hash_password(new_password)
            self.db.update_password(user_data[0], new_hash)
            
            await interaction.followup.send("✅ Пароль успешно изменён!", ephemeral=True)
            logger.info(f"Пользователь {user_data[0]} сменил пароль")

        except Exception as e:
            error_code = generate_error_code()
            logger.error(f"Ошибка смены пароля ({error_code}): {str(e)}", exc_info=True)
            await interaction.followup.send(
                f"🚨 Ошибка {error_code}: Не удалось изменить пароль",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Registration(bot))
    logger.info("Ког регистрации загружен")
