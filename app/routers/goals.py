"""
Room goals router.
"""
from typing import List

from app.db import get_database
from app.schemas.goal import GoalCreate, GoalOut, GoalUpdate
from app.services.goal_service import GoalService
from app.services.room_service import RoomService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    tags=["Goals"],
    responses={404: {"description": "Not found"}},
)


@router.get("/rooms/{room_id}/goals", response_model=List[GoalOut])
async def get_room_goals(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
) -> List[GoalOut]:
    """
    Retrieve all goals for a specific room.

    Args:
        room_id: The ID of the room
        db: Database instance
        user_id: Current user ID

    Returns:
        List[GoalOut]: All goals in the room
    """
    # Ensure the user is a member of the room
    if not await RoomService(db).is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )

    # Fetch and return room goals
    return await GoalService(db).get_room_goals(room_id)



@router.post("/rooms/{room_id}/goals", response_model=GoalOut)
async def create_goal(
    room_id: str,
    goal_data: GoalCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
) -> GoalOut:
    """
    Create a new goal within a room.

    Args:
        room_id: The ID of the room
        goal_data: Data for the new goal
        db: Database instance
        user_id: Current user ID

    Returns:
        GoalOut: The newly created goal
    """
    # Check membership
    if not await RoomService(db).is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )

    # Create and return the goal
    return await GoalService(db).create_goal(room_id, goal_data, user_id)



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
    # Fetch goal to get room_id and verify it exists
    from bson import ObjectId
    try:
        goal_doc = await db.room_goals.find_one({"_id": ObjectId(goal_id)})
    except:
        goal_doc = None
    
    if not goal_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Verify user is a member of the room that owns the goal
    room_service = RoomService(db)
    if not await room_service.is_member(goal_doc["room_id"], user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    service = GoalService(db)
    goal = await service.update_goal(goal_id, goal_data)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    return goal
