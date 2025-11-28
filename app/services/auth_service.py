"""
Authentication service - Simplified for POC (no JWT, basic auth only).
"""
from datetime import datetime
from typing import Optional

from app.schemas.auth import UserLogin, UserOut, UserRegister
from app.utils.security import verify_password, get_password_hash
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize auth service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.users
    
    async def register_user(self, user_data: UserRegister) -> UserOut:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            UserOut: Created user information
        """
        # Check if username already exists
        existing_user = await self.collection.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Create user document
        now = datetime.utcnow()
        hashed_password = get_password_hash(user_data.password)

        user_doc = {
            "username": user_data.username,
            "password": hashed_password,
            "preferred_language": user_data.preferred_language,
            "created_at": now,
            "updated_at": now,
        }
        
        result = await self.collection.insert_one(user_doc)
        
        return UserOut(
            id=str(result.inserted_id),
            username=user_data.username,
            preferred_language=user_data.preferred_language,
            created_at=now.isoformat(),
        )
    
    async def login_user(self, credentials: UserLogin) -> UserOut:
        """
        Authenticate user and return user info (no JWT in POC).
        
        Args:
            credentials: User login credentials
            
        Returns:
            UserOut: User information if login successful
        """
        # Find user by username
        user = await self.collection.find_one({"username": credentials.username})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        return UserOut(
            id=str(user["_id"]),
            username=user["username"],
            preferred_language=user.get("preferred_language", "en"),
            created_at=user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"],
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserOut]:
        """
        Get user information by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[UserOut]: User information if found
        """
        try:
            user = await self.collection.find_one({"_id": ObjectId(user_id)})
        except:
            return None
            
        if not user:
            return None
            
        return UserOut(
            id=str(user["_id"]),
            username=user["username"],
            preferred_language=user.get("preferred_language", "en"),
            created_at=user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"],
        )
    
    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """
        Get user by username (returns raw dict for internal use).
        
        Args:
            username: Username
            
        Returns:
            Optional[dict]: User document or None
        """
        return await self.collection.find_one({"username": username})
