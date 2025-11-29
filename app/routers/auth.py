"""
Authentication router for user registration, login, and profile.
"""

from app.db import get_database
from app.schemas.auth import (PasswordChange, ProfileUpdate, UserLogin,
                              UserOut, UserRegister)
from app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister, db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserOut:
    """
    Register a new user account.

    Args:
        user_data: User registration data (username, password, language)
        db: Database instance

    Returns:
        UserOut: Created user information
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=UserOut)
async def login(
    credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserOut:
    """
    Authenticate user and return user info (POC mode, no JWT).

    Args:
        credentials: Username and password
        db: Database instance

    Returns:
        UserOut: Authenticated user information
    """
    auth_service = AuthService(db)
    return await auth_service.login_user(credentials)


@router.get("/me", response_model=UserOut)
async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_database),
    x_user_id: str = Header(None, alias="X-User-Id"),
) -> UserOut:
    """
    Get current authenticated user information.
    POC mode: Uses X-User-Id header instead of JWT.

    Args:
        db: Database instance
        x_user_id: User ID from header

    Returns:
        UserOut: Current user information
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(x_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.patch("/profile", response_model=UserOut)
async def update_profile(
    profile_data: ProfileUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    x_user_id: str = Header(None, alias="X-User-Id"),
) -> UserOut:
    """
    Update user profile information.

    Args:
        profile_data: Profile update data
        db: Database instance
        x_user_id: User ID from header

    Returns:
        UserOut: Updated user information
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    auth_service = AuthService(db)
    return await auth_service.update_profile(x_user_id, profile_data)


@router.patch("/password")
async def change_password(
    password_data: PasswordChange,
    db: AsyncIOMotorDatabase = Depends(get_database),
    x_user_id: str = Header(None, alias="X-User-Id"),
):
    """
    Change user password.

    Args:
        password_data: Current and new password
        db: Database instance
        x_user_id: User ID from header

    Returns:
        Success message
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    auth_service = AuthService(db)
    await auth_service.change_password(x_user_id, password_data)
    
    return {"message": "Password changed successfully"}
