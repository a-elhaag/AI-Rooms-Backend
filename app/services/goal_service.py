"""
Room goal service for managing room goals.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

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
        self.collection = db.room_goals
    
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
        """
        now = datetime.utcnow()
        goal_id = str(uuid.uuid4())

        goal_doc = {
            "id": goal_id,
            "room_id": room_id,
            "description": goal_data.description,
            "priority": goal_data.priority,
            "status": "active",
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }

        await self.collection.insert_one(goal_doc)

        # Get creator username
        username = "Unknown"
        try:
            user = await self.db.users.find_one({"_id": ObjectId(created_by)})
            if user:
                username = user.get("username")
        except:
            pass

        return GoalOut(
            id=goal_id,
            room_id=room_id,
            description=goal_doc["description"],
            priority=goal_doc["priority"],
            status=goal_doc["status"],
            created_by=created_by,
            created_by_username=username,
            created_at=now.isoformat()
        )
    
    async def get_room_goals(self, room_id: str) -> List[GoalOut]:
        """
        Get all goals for a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            list[GoalOut]: List of goals
        """
        # Sort by priority (descending) and created_at
        cursor = self.collection.find({"room_id": room_id}).sort([
            ("status", 1),  # Active first (by default status order sort of works, but simpler to rely on app logic if needed)
            ("priority", -1),
            ("created_at", -1)
        ])

        goals = []
        async for doc in cursor:
            username = "Unknown"
            try:
                user = await self.db.users.find_one({"_id": ObjectId(doc["created_by"])})
                if user:
                    username = user.get("username")
            except:
                pass

            goals.append(GoalOut(
                id=doc["id"],
                room_id=doc["room_id"],
                description=doc["description"],
                priority=doc["priority"],
                status=doc["status"],
                created_by=doc["created_by"],
                created_by_username=username,
                created_at=doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else doc["created_at"]
            ))

        return goals
    
    async def update_goal(self, goal_id: str, goal_data: GoalUpdate) -> Optional[GoalOut]:
        """
        Update an existing goal.
        
        Args:
            goal_id: Goal ID
            goal_data: Goal update data
            
        Returns:
            Optional[GoalOut]: Updated goal or None
        """
        update_fields = {"updated_at": datetime.utcnow()}

        if goal_data.description is not None:
            update_fields["description"] = goal_data.description
        if goal_data.priority is not None:
            update_fields["priority"] = goal_data.priority
        if goal_data.status is not None:
            update_fields["status"] = goal_data.status

        result = await self.collection.find_one_and_update(
            {"id": goal_id},
            {"$set": update_fields},
            return_document=True
        )

        if not result:
            return None

        username = "Unknown"
        try:
            user = await self.db.users.find_one({"_id": ObjectId(result["created_by"])})
            if user:
                username = user.get("username")
        except:
            pass

        return GoalOut(
            id=result["id"],
            room_id=result["room_id"],
            description=result["description"],
            priority=result["priority"],
            status=result["status"],
            created_by=result["created_by"],
            created_by_username=username,
            created_at=result["created_at"].isoformat() if isinstance(result["created_at"], datetime) else result["created_at"]
        )
