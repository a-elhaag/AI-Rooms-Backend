"""
Tasks router for task management.
"""
from typing import List

from app.db import get_database
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.room_service import RoomService
from app.services.task_service import TaskService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(tags=["Tasks"])


@router.get("/tasks", response_model=List[TaskOut])
async def get_all_user_tasks(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> List[TaskOut]:
    """
    Get all tasks across all rooms the user is a member of.
    
    Args:
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        List[TaskOut]: List of tasks from all user's rooms
    """
    room_service = RoomService(db)
    task_service = TaskService(db)
    
    # Get all rooms user is a member of
    rooms = await room_service.get_user_rooms(current_user_id)
    
    all_tasks = []
    for room in rooms:
        room_tasks = await task_service.get_room_tasks(room.id)
        # Add room name to each task for display
        for task in room_tasks:
            all_tasks.append(TaskOut(
                id=task.id,
                room_id=task.room_id,
                room_name=room.name,
                title=task.title,
                status=task.status,
                assignee_id=task.assignee_id,
                assignee_name=task.assignee_name,
                due_date=task.due_date,
                created_at=task.created_at
            ))
    
    # Sort by created_at descending
    all_tasks.sort(key=lambda t: t.created_at, reverse=True)
    return all_tasks


@router.get("/rooms/{room_id}/tasks", response_model=List[TaskOut])
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
    task = await task_service.create_task(room_id, task_data)
    
    # Broadcast task creation via WebSocket
    from app.routers.ws import manager
    await manager.broadcast_to_room(room_id, {
        "type": "task_created",
        "task": {
            "id": task.id,
            "room_id": task.room_id,
            "title": task.title,
            "status": task.status,
            "assignee_id": task.assignee_id,
            "assignee_name": task.assignee_name,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat() if hasattr(task.created_at, 'isoformat') else str(task.created_at)
        }
    })
    
    return task


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
    
    # Broadcast task update via WebSocket
    from app.routers.ws import manager
    await manager.broadcast_to_room(task.room_id, {
        "type": "task_updated",
        "task": {
            "id": updated_task.id,
            "room_id": updated_task.room_id,
            "title": updated_task.title,
            "status": updated_task.status,
            "assignee_id": updated_task.assignee_id,
            "assignee_name": updated_task.assignee_name,
            "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
            "created_at": updated_task.created_at.isoformat() if hasattr(updated_task.created_at, 'isoformat') else str(updated_task.created_at)
        }
    })
    
    return updated_task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> None:
    """
    Delete a task.
    """
    task_service = TaskService(db)

    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    room_service = RoomService(db)
    if not await room_service.is_member(task.room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )

    deleted = await task_service.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    from app.routers.ws import manager
    await manager.broadcast_to_room(task.room_id, {
        "type": "task_deleted",
        "task_id": task_id,
    })

    return None
