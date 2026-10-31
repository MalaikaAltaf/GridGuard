"""
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.jwt_handler import get_user_id_from_token, get_role_from_token

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts and validates the current user from JWT token.
    Also updates the user's last_seen_at timestamp for availability tracking.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token and extract user ID
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last_seen_at timestamp (for inspector availability tracking)
    user.last_seen_at = datetime.utcnow()
    db.commit()
    
    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based authorization.
    
    Usage:
        @router.get("/admin-only")
        def admin_endpoint(user: User = Depends(require_role(UserRole.OFFICER))):
            ...
    
    Args:
        allowed_roles: One or more UserRole values that are allowed
        
    Returns:
        Dependency function that checks user role
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role: {', '.join(r.value for r in allowed_roles)}"
            )
        return user
    
    return role_checker


# Convenience dependencies for common role checks
def require_officer(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires officer role"""
    if user.role != UserRole.OFFICER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires officer role"
        )
    return user


def require_inspector(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires inspector role"""
    if user.role != UserRole.INSPECTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires inspector role"
        )
    return user
