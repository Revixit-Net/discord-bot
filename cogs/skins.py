import os
import hashlib
import logging
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import DatabaseManager
from utils.helpers import validate_image

logger = logging.getLogger("discord_bot")

class SkinManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.base_path = {
            "skins": "/var/www/site/skins",
            "cloaks": "/var/www/site/cloaks"
        }

    async def get_user_data(self, discord_id: int):
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT username, uuid FROM users WHERE discord_id = ?",
                (discord_id,)
            )
            return cursor.fetchone()

    @app_commands.command(name="upload", description="Загрузить скин/плащ")
    @app_commands.describe(
        asset_type="Тип файла",
        file="PNG файл (макс. 256KB)"
   )
    @app_commands.choices(
        asset_type=[
            app_commands.Choice(name="Скин", value="skins"),
            app_commands.Choice(name="Плащ", value="cloaks")
        ]
    )
    async def upload_asset(
        self,
        interaction: discord.Interaction,
        asset_type: str,
        file: discord.Attachment
    ):
        await interaction.response.defer(ephemeral=True)
        
        user_data = await self.get_user_data(interaction.user.id)
        if not user_data:
            return await interaction.followup.send(
                "❌ Сначала зарегистрируйтесь через /reg",
                ephemeral=True
            )

        # Валидация файла
        error = await validate_image(file)
        if error:
            return await interaction.followup.send(error, ephemeral=True)

        # Сохранение файла
        try:
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            filename = f"{user_data[0]}.png"
            asset_type = asset_type.lower()

            # Пути для сохранения
            web_path = f"{self.base_path[asset_type]}/{filename}"
            temp_path = f"temp/{filename}"

            # Сохраняем во временную папку
            with open(temp_path, "wb") as f:
                f.write(content)

            # Здесь должна быть проверка модератором?
            # ...

            # Переносим в целевую папку
            os.rename(temp_path, web_path)

            # Обновляем БД
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO uploads (user_uuid, skin_hash, cloak_hash)
                    VALUES (?, ?, ?)
                    ON DUPLICATE KEY UPDATE
                        {} = ?,
                        last_updated = CURRENT_TIMESTAMP
                    """.format(f"{asset_type}_hash"),
                    (user_data[1], file_hash, file_hash, file_hash)
                )

            await interaction.followup.send(
                f"✅ {asset_type.capitalize()} успешно загружен!",
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            await interaction.followup.send(
                "⚠ Произошла ошибка при загрузке файла",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(SkinManager(bot))
