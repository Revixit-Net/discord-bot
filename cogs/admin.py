import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.database import DatabaseManager
from utils.helpers import validate_password, hash_password, generate_error_code
from config import Config

logger = logging.getLogger("discord_bot")

class AdminTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.admin_role_id = Config.ADMIN_ROLE_ID

    async def login_autocomplete(
        self, 
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Автодополнение логинов из базы данных."""
        if not self.db.is_connected():
            return [app_commands.Choice(name="🚨 Нет подключения к БД", value="error")]
        
        logins = self.db.search_logins(current)
        return [app_commands.Choice(name=login, value=login) for login in logins[:25]]

    @app_commands.command(
        name="delete",
        description="[ADMIN] Удалить аккаунт пользователя"
    )
    @app_commands.describe(username="Логин пользователя")
    @app_commands.autocomplete(username=login_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_user(
        self,
        interaction: discord.Interaction,
        username: str
    ):
        """Удаление пользователя из базы данных."""
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = self.db.delete_user(username)
            if deleted:
                msg = f"✅ Аккаунт **{username}** удалён!"
                logger.warning(f"Удалён пользователь: {username}")
            else:
                msg = "❌ Пользователь не найден"
            await interaction.followup.send(msg, ephemeral=True)
        except Exception as e:
            error_code = generate_error_code()
            logger.error(f"{error_code} | {str(e)}", exc_info=True)
            await interaction.followup.send(f"🚨 Ошибка {error_code}", ephemeral=True)

    @app_commands.command(
        name="userinfo",
        description="[ADMIN] Информация о пользователе"
    )
    @app_commands.describe(username="Логин пользователя")
    @app_commands.autocomplete(username=login_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def user_info(
        self,
        interaction: discord.Interaction,
        username: str
    ):
        """Получение информации о пользователе."""
        await interaction.response.defer(ephemeral=True)
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT uuid, discord_id, serverID 
                    FROM users 
                    WHERE username = ?""",
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    uuid, discord_id, server_id = result
                    embed = discord.Embed(title=f"Информация о {username}", color=0x00ff00)
                    embed.add_field(name="UUID", value=f"`{uuid}`", inline=False)
                    embed.add_field(name="Discord ID", value=f"`{discord_id}`", inline=False)
                    embed.add_field(name="Сервер", value=server_id, inline=False)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("🔍 Пользователь не найден", ephemeral=True)
        except Exception as e:
            error_code = generate_error_code()
            logger.error(f"{error_code} | {str(e)}", exc_info=True)
            await interaction.followup.send(f"🚨 Ошибка {error_code}", ephemeral=True)

    @app_commands.command(
        name="setpassword",
        description="[ADMIN] Установить новый пароль"
    )
    @app_commands.describe(
        username="Логин пользователя",
        new_password="Новый пароль (мин. 8 символов)"
    )
    @app_commands.autocomplete(username=login_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def admin_set_password(
        self,
        interaction: discord.Interaction,
        username: str,
        new_password: str
    ):
        """Принудительная смена пароля администратором."""
        await interaction.response.defer(ephemeral=True)
        try:
            if error := validate_password(new_password):
                return await interaction.followup.send(f"❌ {error}", ephemeral=True)
            
            new_hash = hash_password(new_password)
            success = self.db.update_password(username, new_hash)
            if success:
                msg = f"✅ Пароль для **{username}** изменён!"
                logger.warning(f"Админ сменил пароль: {username}")
            else:
                msg = "❌ Пользователь не найден"
            await interaction.followup.send(msg, ephemeral=True)
        except Exception as e:
            error_code = generate_error_code()
            logger.error(f"{error_code} | {str(e)}", exc_info=True)
            await interaction.followup.send(f"🚨 Ошибка {error_code}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminTools(bot))
    logger.info("Админские команды загружены")