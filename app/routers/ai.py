"""
AI router for direct AI operations (rewrite, translate, summarize, etc.).
"""

from typing import Optional

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.db import get_database

router = APIRouter(prefix="/ai", tags=["AI"])


class RewriteRequest(BaseModel):
    """Request schema for text rewriting."""

    text: str = Field(..., min_length=1)


class RewriteResponse(BaseModel):
    """Response schema for text rewriting."""

    original: str
    rewritten: str


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


from app.ai.tools import tool_summarize_messages, tool_translate_text


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_text(
    request: RewriteRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> RewriteResponse:
    """
    Rewrite text using user's personal style.

    Args:
        request: Text to rewrite
        db: Database instance

    Returns:
        RewriteResponse: Original and rewritten text
    """
    # Placeholder for now - just echo
    return RewriteResponse(
        original=request.text, rewritten=f"[Rewritten]: {request.text}"
    )


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(
    request: TranslateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
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
    # TODO: Add current_user dependency
) -> SummarizeResponse:
    """
    Summarize recent messages in a room.

    Args:
        request: Room ID and message count
        db: Database instance

    Returns:
        SummarizeResponse: Room summary
    """
    summary = await tool_summarize_messages(
        db, request.room_id, request.last_n_messages
    )

    return SummarizeResponse(room_id=request.room_id, summary=summary)


@router.post("/debug")
async def debug_ai(
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> dict:
    """
    Debug endpoint for AI agent decisions.

    Returns:
        dict: Debug information

    TODO:
        - Return AI agent state, recent decisions, etc.
        - This is for debugging during development
    """
    pass
