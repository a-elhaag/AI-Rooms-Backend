"""
Tasks router for task management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.room_service import RoomService
from app.services.task_service import TaskService
from app.utils.security import get_current_user_id

router = APIRouter(tags=["Tasks"])


@router.get("/rooms/{room_id}/tasks", response_model=list[TaskOut])
async def get_room_tasks(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> list[TaskOut]:
    """
    Get all tasks for a room.
    
    Args:
        room_id: Room ID
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        list[TaskOut]: List of tasks
    """
    
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    task_service = TaskService(db)
    return await task_service.get_room_tasks(room_id)


@router.post("/rooms/{room_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    room_id: str,
    task_data: TaskCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> TaskOut:
    """
    Create a new task in a room.
    
    Args:
        room_id: Room ID
        task_data: Task creation data
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        TaskOut: Created task information
    """
    
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    task_service = TaskService(db)
    return await task_service.create_task(room_id, task_data)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> TaskOut:
    """
    Update an existing task.
    
    Args:
        task_id: Task ID
        task_data: Task update data
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        TaskOut: Updated task information
    """
    
    task_service = TaskService(db)
    
    # Get task to verify room membership
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify user is a member of the task's room
    room_service = RoomService(db)
    if not await room_service.is_member(task.room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    updated_task = await task_service.update_task(task_id, task_data)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return updated_task
