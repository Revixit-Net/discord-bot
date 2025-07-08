import discord
import logging
from discord import Intents
from discord.ext.commands import Bot
from config import Config
from cogs.registration import Registration
from cogs.admin import AdminTools


# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord_bot")

# Инициализация бота
intents = Intents.default()
intents.message_content = True
intents.members = True

bot = Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Обработчик события запуска бота"""
    logger.info(f"Запуск бота {bot.user} | ID: {bot.user.id}")
    await load_cogs()
    await bot.tree.sync()
    logger.info("Слеш-команды синхронизированы")

async def load_cogs():
    """Загрузка модулей"""
    await bot.add_cog(Registration(bot))
    await bot.add_cog(AdminTools(bot))
    logger.info("Все модули загружены")

if __name__ == "__main__":
    bot.run(Config.BOT_TOKEN)
