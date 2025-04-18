import logging
import discord
from discord.ext import commands
from config import Config
from cogs.registration import Registration
from cogs.admin import AdminTools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discord_bot")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    logger.info(f"============================================================================ GST ============================================================================")
    logger.info(f"Бот {bot.user} запущен! ID: {bot.user.id}")
    await setup()

async def setup():
    await bot.add_cog(Registration(bot))
    await bot.add_cog(AdminTools(bot))
    logger.info("Модули успешно загружены")

bot.run(Config.BOT_TOKEN)