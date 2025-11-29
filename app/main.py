import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import close_mongo_connection, connect_to_mongo
from app.routers import (
    ai,
    auth,
    documents,
    goals,
    kb,
    messages,
    profiles,
    rooms,
    tasks,
    ws,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AI Rooms API...")
    try:
        await connect_to_mongo()
        logger.info("✓ Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

    yield

    # Shutdown
    await close_mongo_connection()
    logger.info("✓ Closed MongoDB connection")


# Initialize FastAPI app
app = FastAPI(
    title="AI Rooms API",
    description="AI-powered multi-room chat and task management system",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
# Allow all origins for development / testing. To restrict origins in production,
# replace the following with:
# cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(rooms.router)
app.include_router(goals.router)
app.include_router(kb.router)
app.include_router(documents.router)
app.include_router(messages.router)
app.include_router(tasks.router)
app.include_router(ai.router)
app.include_router(ws.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"message": "AI Rooms API", "version": "0.1.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
