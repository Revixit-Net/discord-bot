import uuid
import bcrypt
import re
import secrets
from typing import Optional

def generate_uuid(username: str) -> str:
    return str(uuid.uuid3(uuid.NAMESPACE_OID, f"OfflinePlayer:{username}"))

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