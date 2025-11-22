"""
Authentication service - Simplified for POC (no JWT, basic auth only).
"""
from datetime import datetime
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.auth import UserLogin, UserOut, UserRegister
from app.utils.security import verify_password


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize auth service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
    
    async def register_user(self, user_data: UserRegister) -> UserOut:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            UserOut: Created user information
            
        TODO: 
            - Check if username already exists
            - Store password (plain text in POC - use hashing in production!)
            - Create user document in users collection
            - Create default user profile
            - Return user information
        """
        pass
    
    async def login_user(self, credentials: UserLogin) -> UserOut:
        """
        Authenticate user and return user info (no JWT in POC).
        
        Args:
            credentials: User login credentials
            
        Returns:
            UserOut: User information if login successful
            
        TODO:
            - Find user by username
            - Verify password using verify_password()
            - Return user information or raise HTTPException
        """
        pass
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserOut]:
        """
        Get user information by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[UserOut]: User information if found
            
        TODO:
            - Query users collection by _id
            - Return user data or None
        """
        pass
    
    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """
        Get user by username (returns raw dict for internal use).
        
        Args:
            username: Username
            
        Returns:
            Optional[dict]: User document or None
            
        TODO:
            - Query users collection by username
            - Return user document or None
        """
        pass
