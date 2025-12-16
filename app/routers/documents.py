"""
Documents router for file upload and RAG operations.
"""
from typing import List, Optional

from app.db import get_database
from app.services.auth_service import AuthService
from app.services.rag_service import DocumentOut, RAGService
from app.services.room_service import RoomService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    prefix="/rooms/{room_id}/documents",
    tags=["Documents"],
    responses={404: {"description": "Not found"}},
)

# Allowed file types
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.ms-powerpoint": "ppt",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("", response_model=DocumentOut)
async def upload_document(
    room_id: str,
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload a document (PDF or PowerPoint) for RAG processing.
    """
    # Verify user is member of room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    # Validate file type
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: PDF, PowerPoint"
        )
    
    file_type = ALLOWED_TYPES[content_type]
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Get username
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    username = user.username if user else None
    
    # Process document
    rag_service = RAGService(db)
    try:
        document = await rag_service.process_document(
            room_id=room_id,
            filename=file.filename,
            file_content=content,
            file_type=file_type,
            user_id=user_id,
            username=username
        )
    except Exception as e:
        print(f"[upload_document] Error processing document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document"
        )
    
    # Broadcast document upload via WebSocket
    from app.routers.ws import manager
    await manager.broadcast_to_room(room_id, {
        "type": "document_uploaded",
        "document": {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "summary": document.summary,
            "uploaded_by_name": document.uploaded_by_name,
            "created_at": document.created_at
        }
    })
    
    return document


@router.get("", response_model=List[DocumentOut])
async def get_room_documents(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all documents for a room.
    """
    # Verify user is member of room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    rag_service = RAGService(db)
    return await rag_service.get_room_documents(room_id)


@router.post("/search")
async def search_documents(
    room_id: str,
    query: str,
    limit: int = 5,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Semantic search across room documents.
    """
    # Verify user is member of room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    rag_service = RAGService(db)
    results = await rag_service.semantic_search(room_id, query, limit)
    
    return {"results": results}


@router.post("/ask")
async def ask_documents(
    room_id: str,
    question: str,
    document_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Ask a question about documents using RAG.
    """
    # Verify user is member of room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    rag_service = RAGService(db)
    answer = await rag_service.ask_document(room_id, question, document_id)
    
    return {"answer": answer, "question": question}


@router.delete("/{document_id}")
async def delete_document(
    room_id: str,
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a document and its chunks.
    """
    # Verify user is member of room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    rag_service = RAGService(db)
    success = await rag_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Broadcast document deletion
    from app.routers.ws import manager
    await manager.broadcast_to_room(room_id, {
        "type": "document_deleted",
        "document_id": document_id
    })
    
    return {"success": True, "message": "Document deleted"}
