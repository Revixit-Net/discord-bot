import uuid
import bcrypt
import re
import discord
import secrets
from typing import Optional
from PIL import Image
import io

async def validate_image(file: discord.Attachment) -> str:
    """Проверка PNG файла"""
    if file.size > 256 * 1024:
        return "❌ Файл слишком большой (макс. 256KB)"
    
    if not file.filename.lower().endswith('.png'):
        return "❌ Только PNG файлы разрешены"
    
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        if img.format != 'PNG':
            return "❌ Это не PNG файл"
            
        # Проверка размеров для скина
        if img.size != (64, 64):
            return "❌ Неверный размер (требуется 64x64)"

    except Exception:
        return "❌ Некорректный файл изображения"
    
    return None

def generate_error_code(length: int = 6) -> str:
    return secrets.token_hex(length // 2 + 1)[:length].upper()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def validate_username(username: str) -> Optional[str]:
    if not 3 <= len(username) <= 16:
        return "Длина логина должна быть от 3 до 16 символов"
    
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return "Логин может содержать только буквы, цифры и подчёркивание"
    
    return None

def validate_password(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Пароль должен содержать минимум 8 символов"
    
    if not any(c.isupper() for c in password):
        return "Пароль должен содержать хотя бы одну заглавную букву"
    
    if not any(c.isdigit() for c in password):
        return "Пароль должен содержать хотя бы одну цифру"
    
    return None

def generate_access_token() -> str:
    return str(uuid.uuid4())

def sanitize_input(text: str) -> str:
    return text.strip()[:32]

def format_player_uuid(uuid_str: str) -> str:
    return str(uuid.UUID(uuid_str))