"""
AI router for direct AI operations (rewrite, translate, summarize, etc.).
"""

from datetime import datetime
from typing import Optional

from app.db import get_database
from app.services.room_service import RoomService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["AI"])


class RephraseRequest(BaseModel):
    """Request schema for text rephrasing."""

    text: str = Field(..., min_length=1)
    style: str = Field(default="professional")


class RephraseResponse(BaseModel):
    """Response schema for text rephrasing."""

    original: str
    rephrased: str


class TranslateRequest(BaseModel):
    """Request schema for translation."""

    text: str = Field(..., min_length=1)
    target_language: Optional[str] = None


class TranslateResponse(BaseModel):
    """Response schema for translation."""

    original: str
    translated: str
    target_language: str


class SummarizeRequest(BaseModel):
    """Request schema for room summarization."""

    room_id: str
    last_n_messages: int = Field(default=20, ge=1, le=100)


class SummarizeResponse(BaseModel):
    """Response schema for room summarization."""

    room_id: str
    summary: str


from app.ai.tools import (tool_rephrase_text, tool_summarize_messages,
                          tool_translate_text, tool_update_room_kb)
from app.models.kb import KnowledgeBaseResponse


@router.post("/rephrase", response_model=RephraseResponse)
async def rephrase_text(
    request: RephraseRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> RephraseResponse:
    """
    Rephrase text in a specific style.

    Args:
        request: Text to rephrase
        db: Database instance

    Returns:
        RephraseResponse: Original and rephrased text
    """
    rephrased = await tool_rephrase_text(request.text, request.style)
    return RephraseResponse(original=request.text, rephrased=rephrased)


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(
    request: TranslateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> TranslateResponse:
    """
    Translate text to target language.

    Args:
        request: Text and optional target language
        db: Database instance

    Returns:
        TranslateResponse: Original and translated text
    """
    target_lang = request.target_language or "en"
    translated = await tool_translate_text(request.text, target_lang)

    return TranslateResponse(
        original=request.text, translated=translated, target_language=target_lang
    )


@router.post("/summarize-room", response_model=SummarizeResponse)
async def summarize_room(
    request: SummarizeRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> SummarizeResponse:
    """
    Summarize recent messages in a room.

    Args:
        request: Room ID and message count
        db: Database instance
        current_user_id: Current user ID from header

    Returns:
        SummarizeResponse: Room summary
    """
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(request.room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    summary = await tool_summarize_messages(
        db, request.room_id, request.last_n_messages
    )

    return SummarizeResponse(room_id=request.room_id, summary=summary)


class UpdateKBRequest(BaseModel):
    """Request schema for updating the Knowledge Base."""

    room_id: str
    summary: Optional[str] = None
    key_decision: Optional[str] = None
    important_link: Optional[str] = None


@router.post("/update-kb", response_model=KnowledgeBaseResponse)
async def update_kb(
    request: UpdateKBRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> KnowledgeBaseResponse:
    """
    Update the Knowledge Base for a room.

    Args:
        request: UpdateKBRequest containing room_id and optional fields to update
        db: Database instance
        current_user_id: Current user ID from header

    Returns:
        KnowledgeBaseResponse: Updated Knowledge Base
    """
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(request.room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    updated_kb = await tool_update_room_kb(
        db,
        request.room_id,
        summary=request.summary,
        key_decision=request.key_decision,
        important_link=request.important_link,
    )
    return KnowledgeBaseResponse(**updated_kb)


class ChatRequest(BaseModel):
    """Request schema for AI chat."""
    
    room_id: str
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Response schema for AI chat."""
    
    content: str
    action: str = "message"  # message, task_created, etc.


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> ChatResponse:
    """
    Chat with AI assistant. AI can automatically detect when to:
    - Reply with information
    - Create tasks
    - Search the web
    - Translate text
    - Summarize conversations
    
    Args:
        request: Chat request with room_id and message
        db: Database instance
        current_user_id: Current user ID from header
    
    Returns:
        ChatResponse: AI response
    """
    from app.ai.orchestrator import AIOrchestrator

    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(request.room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    # Handle with AI orchestrator
    orchestrator = AIOrchestrator(db)
    result = await orchestrator.handle_message(
        room_id=request.room_id,
        user_id=current_user_id,
        content=request.message,
        message_id=""  # Will be set if called from WebSocket
    )
    
    if not result:
        return ChatResponse(
            content="I'm not configured yet. Please set the GOOGLE_API_KEY.",
            action="message"
        )
    
    return ChatResponse(
        content=result.get("content", "I'm thinking..."),
        action=result.get("action", "message")
    )


@router.post("/debug")
async def debug_ai(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> dict:
    """
    Debug endpoint for AI agent decisions.

    Returns:
        dict: Debug information

    Note:
        - Use this endpoint for internal debugging during development.
    """
    return {
        "status": "debug_endpoint_placeholder",
        "message": "AI debug functionality not yet implemented",
        "timestamp": datetime.utcnow().isoformat()
    }
