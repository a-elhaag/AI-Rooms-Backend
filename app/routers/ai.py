"""
AI router for direct AI operations (rewrite, translate, summarize, etc.).
"""

from typing import Optional

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.db import get_database

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


from app.ai.tools import (
    tool_rephrase_text,
    tool_summarize_messages,
    tool_translate_text,
)


@router.post("/rephrase", response_model=RephraseResponse)
async def rephrase_text(
    request: RephraseRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
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
) -> dict:
    """
    Debug endpoint for AI agent decisions.

    Returns:
        dict: Debug information

    Note:
        - Use this endpoint for internal debugging during development.
    """
    pass
