import os
import hmac
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from backend.config import Config

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt (or PBKDF2-HMAC-SHA256 fallback)."""
    if _HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        salt = os.urandom(16)
        kdf = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return "pbkdf2$" + salt.hex() + "$" + kdf.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    if not hashed_password or not plain_password:
        return False
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            if _HAS_BCRYPT:
                return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
            return False
        elif hashed_password.startswith("pbkdf2$"):
            _, salt_hex, hash_hex = hashed_password.split("$")
            salt = bytes.fromhex(salt_hex)
            test_kdf = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
            return hmac.compare_digest(test_kdf.hex(), hash_hex)
        else:
            # Fallback direct comparison or sha256
            test_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
            return hmac.compare_digest(test_hash, hashed_password)
    except Exception:
        return False

def generate_jwt_token(user_id: int, role: str = "user") -> str:
    """Generate signed JWT token."""
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")

def decode_jwt_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}
