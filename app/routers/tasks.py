"""
Tasks router for task management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.room_service import RoomService
from app.services.task_service import TaskService

router = APIRouter(tags=["Tasks"])


@router.get("/rooms/{room_id}/tasks", response_model=list[TaskOut])
async def get_room_tasks(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> list[TaskOut]:
    """
    Get all tasks for a room.
    
    Args:
        room_id: Room ID
        db: Database instance
        
    Returns:
        list[TaskOut]: List of tasks
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize RoomService and verify user is member
        - Initialize TaskService
        - Call get_room_tasks method
        - Return list of tasks
    """
    pass


@router.post("/rooms/{room_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    room_id: str,
    task_data: TaskCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> TaskOut:
    """
    Create a new task in a room.
    
    Args:
        room_id: Room ID
        task_data: Task creation data
        db: Database instance
        
    Returns:
        TaskOut: Created task information
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize RoomService and verify user is member
        - Initialize TaskService
        - Call create_task method
        - Return task information
    """
    pass


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> TaskOut:
    """
    Update an existing task.
    
    Args:
        task_id: Task ID
        task_data: Task update data
        db: Database instance
        
    Returns:
        TaskOut: Updated task information
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize TaskService
        - Get task and verify user is member of the room
        - Call update_task method
        - Return updated task or 404 error
    """
    pass
