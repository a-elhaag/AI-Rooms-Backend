"""
Database connection and utilities for MongoDB.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

# Global MongoDB client instance
_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    """
    Initialize MongoDB connection with connection pooling.
    """
    global _client
    settings = get_settings()

    # Configure connection pooling to enhance performance
    _client = AsyncIOMotorClient(
        settings.MONGO_URI,
        minPoolSize=10,
        maxPoolSize=100
    )

    # Verify connection
    try:
        await _client.admin.command('ping')
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB: {e}")


async def close_mongo_connection() -> None:
    """
    Close MongoDB connection.
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
