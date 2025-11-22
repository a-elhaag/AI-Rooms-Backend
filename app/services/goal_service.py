"""
Room goal service for managing room goals.
"""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.goal import GoalCreate, GoalOut, GoalUpdate


class GoalService:
    """Service for room goal operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize goal service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
    
    async def create_goal(
        self,
        room_id: str,
        goal_data: GoalCreate,
        created_by: str
    ) -> GoalOut:
        """
        Create a new goal for a room.
        
        Args:
            room_id: Room ID
            goal_data: Goal creation data
            created_by: User ID creating the goal
            
        Returns:
            GoalOut: Created goal information
            
        TODO:
            - Create goal document in room_goals collection
            - Set default status to "active"
            - Return goal with creator username
        """
        pass
    
    async def get_room_goals(self, room_id: str) -> list[GoalOut]:
        """
        Get all goals for a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            list[GoalOut]: List of goals
            
        TODO:
            - Query room_goals collection for room_id
            - Join with users to get creator username
            - Sort by priority (descending) and created_at
            - Return list of goals
        """
        pass
    
    async def update_goal(self, goal_id: str, goal_data: GoalUpdate) -> Optional[GoalOut]:
        """
        Update an existing goal.
        
        Args:
            goal_id: Goal ID
            goal_data: Goal update data
            
        Returns:
            Optional[GoalOut]: Updated goal or None
            
        TODO:
            - Find goal by _id
            - Update fields that are not None
            - Return updated goal
        """
        pass
