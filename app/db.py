"""
Database connection and utilities for MongoDB.
"""
from typing import Any

from motor.motor_asyncio import (AsyncIOMotorClient, AsyncIOMotorCollection,
                                 AsyncIOMotorDatabase)

from app.config import get_settings

# Global MongoDB client instance
_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    """
    Initialize MongoDB connection.
    
    TODO: Add connection pooling configuration
    TODO: Add connection error handling and retry logic
    """
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    # TODO: Test connection
    pass


async def close_mongo_connection() -> None:
    """
    Close MongoDB connection.
    
    TODO: Implement graceful connection closure
    """
    global _client
    if _client:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance.
    
    Returns:
        AsyncIOMotorDatabase: Database instance
        
    Raises:
        RuntimeError: If database connection is not initialized
    """
    if _client is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    
    settings = get_settings()
    return _client[settings.MONGO_DB_NAME]


# Collection accessor functions

def get_users_collection() -> AsyncIOMotorCollection:
    """Get users collection."""
    return get_database()["users"]


def get_rooms_collection() -> AsyncIOMotorCollection:
    """Get rooms collection."""
    return get_database()["rooms"]


def get_room_members_collection() -> AsyncIOMotorCollection:
    """Get room_members collection."""
    return get_database()["room_members"]


def get_messages_collection() -> AsyncIOMotorCollection:
    """Get messages collection."""
    return get_database()["messages"]


def get_tasks_collection() -> AsyncIOMotorCollection:
    """Get tasks collection."""
    return get_database()["tasks"]


def get_user_profiles_collection() -> AsyncIOMotorCollection:
    """Get user_profiles collection."""
    return get_database()["user_profiles"]


def get_room_goals_collection() -> AsyncIOMotorCollection:
    """Get room_goals collection."""
    return get_database()["room_goals"]


def get_room_kb_collection() -> AsyncIOMotorCollection:
    """Get room_kb collection."""
    return get_database()["room_kb"]
