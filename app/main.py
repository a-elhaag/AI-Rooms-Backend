from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.db import close_mongo_connection, connect_to_mongo
from app.routers import ai, auth, messages, rooms, tasks, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    print("✓ Connected to MongoDB")

    yield

    # Shutdown
    await close_mongo_connection()
    print("✓ Closed MongoDB connection")


# Initialize FastAPI app
app = FastAPI(
    title="AI Rooms API",
    description="AI-powered multi-room chat and task management system",
    version="0.1.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(rooms.router)
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
