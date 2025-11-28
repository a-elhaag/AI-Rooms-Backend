"""
Security utilities - Password hashing.
"""
from passlib.context import CryptContext

# Create a CryptContext object
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a password hash.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


# Dependency for getting current user ID from header (POC mode)
from fastapi import Header, HTTPException, status


def get_current_user_id(x_user_id: str = Header(None, alias="X-User-Id")) -> str:
    """
    Dependency to get current user ID from X-User-Id header (POC mode).
    
    Args:
        x_user_id: User ID from header
        
    Returns:
        str: User ID
        
    Raises:
        HTTPException: If header is missing
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header is required"
        )
    return x_user_id
