import bcrypt
import jwt
from datetime import datetime, timedelta
from app.core.config import settings

class SecurityUtils:
    """Handles password hashing and JWT-based authentication."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a password with bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verifies a password against its hashed version."""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    @staticmethod
    def generate_jwt(payload: dict, expires_in: int = 3600) -> str:
        """Generates a JWT token with expiration."""
        payload["exp"] = datetime.utcnow() + timedelta(seconds=expires_in)
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode_jwt(token: str) -> dict:
        """Decodes a JWT token and returns its payload."""
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}
