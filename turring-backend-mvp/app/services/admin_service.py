"""Admin authentication service for TurringChat.

This module handles admin authentication using JWT tokens.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt

# Admin credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
# Pre-computed bcrypt hash for "admin123" - change via ADMIN_PASSWORD_HASH env var
# To generate a new hash: python3 -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$RZI94bkNCR6WZg6oF69WG.k8Wtp5C7E6amTtk6YOK3x1jrZtLGidu")  # admin123
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def verify_admin_password(username: str, password: str) -> bool:
    """Verify admin username and password.

    Args:
        username: Admin username
        password: Plain text password

    Returns:
        True if credentials are valid, False otherwise
    """
    if username != ADMIN_USERNAME:
        return False

    # bcrypt.checkpw requires bytes
    password_bytes = password.encode('utf-8')
    hash_bytes = ADMIN_PASSWORD_HASH.encode('utf-8')

    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_admin_token(username: str) -> str:
    """Create a JWT token for authenticated admin.

    Args:
        username: Admin username

    Returns:
        JWT token string
    """
    payload = {
        "sub": username,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_admin_token(token: str) -> Optional[dict]:
    """Verify and decode an admin JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Verify it's an admin token
        if payload.get("role") != "admin":
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_password(password: str) -> str:
    """Hash a password for storage.

    Utility function for generating password hashes.

    Args:
        password: Plain text password

    Returns:
        Bcrypt password hash
    """
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')
