"""
JWT token creation and verification
"""
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from app.config import settings
from app.models.user import UserRole


def create_token(user_id: UUID, role: UserRole) -> str:
    """
    Create a JWT token for authenticated user.
    
    Args:
        user_id: User's UUID
        role: User's role (officer, inspector, circle_manager)
        
    Returns:
        Encoded JWT token string
    """
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "role": role.value,
        "exp": datetime.utcnow() + timedelta(days=settings.jwt_expiry_days),
        "iat": datetime.utcnow(),  # Issued at
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract user ID from a valid JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User UUID if token is valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None
    
    try:
        user_id = UUID(payload.get("sub"))
        return user_id
    except (ValueError, TypeError):
        return None


def get_role_from_token(token: str) -> Optional[str]:
    """
    Extract user role from a valid JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User role string if token is valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None
    
    return payload.get("role")
