"""
Room goals router.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.schemas.goal import GoalCreate, GoalOut, GoalUpdate
from app.services.goal_service import GoalService
from app.utils.security import get_current_user_id

router = APIRouter(
    tags=["Goals"],
    responses={404: {"description": "Not found"}},
)


@router.get("/rooms/{room_id}/goals", response_model=List[GoalOut])
async def get_room_goals(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all goals for a room.
    """
    # TODO: Check if user is member of room
    service = GoalService(db)
    goals = await service.get_room_goals(room_id)
    return goals


@router.post("/rooms/{room_id}/goals", response_model=GoalOut)
async def create_goal(
    room_id: str,
    goal_data: GoalCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new goal for a room.
    """
    # TODO: Check if user is member of room
    service = GoalService(db)
    goal = await service.create_goal(room_id, goal_data, user_id)
    return goal


@router.put("/goals/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: str,
    goal_data: GoalUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update an existing goal.
    """
    # TODO: Check if user is member of room that owns the goal
    service = GoalService(db)
    goal = await service.update_goal(goal_id, goal_data)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    return goal
