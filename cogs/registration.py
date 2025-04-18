import discord
import mariadb
import logging
import uuid
import bcrypt
from discord.ext import commands
from utils.database import DatabaseManager
from utils.helpers import generate_uuid
from utils.helpers import generate_error_code

logger = logging.getLogger("discord_bot")

class Registration(commands.Cog):
    async def send_error_response(self, ctx, error_message, exception=None):
        error_code = generate_error_code()
        error_msg = f"🚨 **Ошибка {error_code}**: {error_message}"
        
        # Логирование с кодом
        logger.error(
            f"Код ошибки: {error_code} | "
            f"Пользователь: {ctx.author.id} | "
            f"Ошибка: {str(exception)}",
            exc_info=bool(exception)
        )

        await ctx.send(error_msg)
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @commands.command(name="register")
    async def start_registration(self, ctx):
        try:
            await ctx.author.send(
                "🎮 **Регистрация игрового аккаунта**\n"
                "Для регистрации введите в ЛС команду:\n"
                "`!reg <логин> <пароль>`\n\n"
                "**Требования:**\n"
                "• Логин: 3-16 символов (a-z, 0-9, _)\n"
                "• Пароль: минимум 8 символов\n"
                "Пример: `!reg Alexei_123 sTr0ngP@ss`"
            )
            logger.info(f"Отправлены инструкции для {ctx.author.id}")

        except discord.Forbidden:
            await ctx.send("🔔 Включите личные сообщения для регистрации!")
            logger.warning(f"Не удалось отправить ЛС пользователю {ctx.author.id}")

    @commands.command(name="reg")
    @commands.dm_only()
    async def process_registration(self, ctx, login: str, password: str):
        logger.info(f"Начата регистрация: {ctx.author.id} | Логин: {login}")

        try:
            # Валидация логина
            if not 3 <= len(login) <= 16:
                raise commands.BadArgument("Логин должен быть от 3 до 16 символов")

            if not login.isalnum() and '_' not in login:
                raise commands.BadArgument("Логин содержит запрещённые символы")

            # Валидация пароля
            if len(password) < 8:
                raise commands.BadArgument("Пароль слишком короткий (минимум 8 символов)")

            # Проверка существующего аккаунта
            existing = self.db.check_existing_user(ctx.author.id, login)
            if existing:
                logger.warning(f"Попытка повторной регистрации: {ctx.author.id}")
                return await ctx.send("❌ У вас уже есть аккаунт или логин занят!")

            # Генерация данных
            user_data = (
                login,
                self.hash_password(password),
                str(uuid.uuid4()),  # accessToken
                generate_uuid(login),  # UUID
                ctx.author.id,
                "default"  # serverID
            )

            # Сохранение в БД
            self.db.add_user(user_data)
            
            logger.info(f"Успешная регистрация: {login} ({ctx.author.id})")
            await ctx.send(f"✅ Аккаунт **{login}** успешно создан!\n"
                          f"Используйте логин и пароль в лаунчере.")

        except mariadb.IntegrityError as e:
            await self.send_error_response(
                ctx, 
                "Конфликт данных. Логин уже занят.",
                e
            )
        
        except commands.BadArgument as e:
            await self.send_error_response(
                ctx,
                f"Некорректные данные: {str(e)}",
                e
            )
        
        except Exception as e:
            await self.send_error_response(
                ctx,
                "Внутренняя ошибка сервера. Просьба отправить репорт об ошибке в канал https://ptb.discord.com/channels/1224402434160595027/1230213959525601420 .",
                e
            )

    @process_registration.error
    async def reg_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Неправильный формат команды! Пример: `!reg Alexei password`")
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("🚫 Используйте команду в личных сообщениях бота!")

async def setup(bot):
    await bot.add_cog(Registration(bot))
    logger.info("Ког регистрации загружен")