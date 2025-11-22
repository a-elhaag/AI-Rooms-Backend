"""
Authentication router for user registration, login, and profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserOut:
    """
    Register a new user account.
    
    Args:
        user_data: User registration data (username, password, language)
        db: Database instance
        
    Returns:
        UserOut: Created user information
        
    TODO:
        - Initialize AuthService
        - Call register_user method
        - Handle username already exists error
        - Return user information
    """
    pass


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Token:
    """
    Authenticate user and return JWT token.
    
    Args:
        credentials: Username and password
        db: Database instance
        
    Returns:
        Token: JWT access token
        
    TODO:
        - Initialize AuthService
        - Call login_user method
        - Handle invalid credentials error
        - Return JWT token
    """
    pass


@router.get("/me", response_model=UserOut)
async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add JWT token dependency here
) -> UserOut:
    """
    Get current authenticated user information.
    
    Args:
        db: Database instance
        
    Returns:
        UserOut: Current user information
        
    TODO:
        - Create dependency to extract and verify JWT token
        - Get user_id from token
        - Initialize AuthService
        - Call get_current_user method
        - Return user information or 401 error
    """
    pass
