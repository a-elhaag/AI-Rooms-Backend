"""
Task service for task management.
"""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.task import TaskCreate, TaskOut, TaskUpdate


class TaskService:
    """Service for task operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize task service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
    
    async def create_task(self, room_id: str, task_data: TaskCreate) -> TaskOut:
        """
        Create a new task in a room.
        
        Args:
            room_id: Room ID
            task_data: Task creation data
            
        Returns:
            TaskOut: Created task information
            
        TODO:
            - Create task document in tasks collection
            - Set default status to "todo"
            - Return task information with assignee name if applicable
        """
        pass
    
    async def get_room_tasks(self, room_id: str) -> list[TaskOut]:
        """
        Get all tasks for a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            list[TaskOut]: List of tasks
            
        TODO:
            - Query tasks collection for room_id
            - Join with users to get assignee names
            - Return list of tasks
        """
        pass
    
    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Optional[TaskOut]:
        """
        Update an existing task.
        
        Args:
            task_id: Task ID
            task_data: Task update data
            
        Returns:
            Optional[TaskOut]: Updated task or None if not found
            
        TODO:
            - Find task by _id
            - Update fields that are not None
            - Return updated task information
        """
        pass
    
    async def get_task_by_id(self, task_id: str) -> Optional[TaskOut]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Optional[TaskOut]: Task information or None
            
        TODO:
            - Query tasks collection by _id
            - Return task information
        """
        pass
