"""
Security utilities - Password hashing.
"""
import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches
    """
    try:
        # Convert to bytes and truncate to 72 bytes for bcrypt compatibility
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Generate a password hash.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')


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
