import discord
from discord.ext import commands
import logging
from utils.database import DatabaseManager
from config import Config

logger = logging.getLogger("discord_bot")

class AdminTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.admin_role_id = Config.ADMIN_ROLE_ID

    async def cog_check(self, ctx):
        if not any(role.id == self.admin_role_id for role in ctx.author.roles):
            logger.warning(f"Попытка доступа к админ-командам: {ctx.author} (ID: {ctx.author.id})")
            raise commands.MissingPermissions(["administrator"])
        return True

    @commands.command(name="delete_user", help="Удалить аккаунт пользователя по логину")
    async def delete_user(self, ctx, username: str):
        logger.info(f"Запрос на удаление от {ctx.author}: пользователь {username}")

        try:
            deleted_count = self.db.delete_user(username)
            
            if deleted_count > 0:
                logger.warning(f"Успешное удаление: {username} | Инициатор: {ctx.author.id}")
                await ctx.send(f"✅ Аккаунт `{username}` успешно удалён!")
            else:
                logger.info(f"Попытка удаления несуществующего аккаунта: {username}")
                await ctx.send("❌ Пользователь не найден в базе данных!")

        except Exception as e:
            logger.error(f"Ошибка при удалении {username}: {str(e)}", exc_info=True)
            await ctx.send("⚠ Произошла ошибка при выполнении операции!")

    @commands.command(name="user_info", help="Получить информацию о пользователе")
    async def get_user_info(self, ctx, username: str):
        logger.info(f"Запрос информации о пользователе: {username}")

        try:
            with self.db as cursor:
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
                    
                    logger.debug(f"Успешный запрос информации: {username}")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("🔍 Пользователь не найден")

        except Exception as e:
            logger.error(f"Ошибка получения информации: {str(e)}")
            await ctx.send("⚠ Ошибка при получении данных")

    @delete_user.error
    @get_user_info.error
    async def admin_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Не указан обязательный аргумент: `{error.param.name}`")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Недостаточно прав для выполнения команды!")
        else:
            await ctx.send("⚠ Произошла непредвиденная ошибка!")

async def setup(bot):
    await bot.add_cog(AdminTools(bot))
    logger.info("Админские команды успешно загружены")