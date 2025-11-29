"""
Task service for task management.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

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
        self.collection = db.tasks
    
    async def create_task(self, room_id: str, task_data: TaskCreate) -> TaskOut:
        """
        Create a new task in a room.
        
        Args:
            room_id: Room ID
            task_data: Task creation data
            
        Returns:
            TaskOut: Created task information
        """
        now = datetime.utcnow()
        task_id = str(uuid.uuid4())

        task_doc = {
            "id": task_id,
            "room_id": room_id,
            "title": task_data.title,
            "status": "todo",
            "assignee_id": task_data.assignee_id,
            "due_date": task_data.due_date,
            "created_at": now,
            "updated_at": now
        }

        await self.collection.insert_one(task_doc)

        # Determine assignee name
        assignee_name = None
        if task_data.assignee_id:
            if task_data.assignee_id == "ai":
                assignee_name = "AI"
            else:
                try:
                    user = await self.db.users.find_one({"_id": ObjectId(task_data.assignee_id)})
                    if user:
                        assignee_name = user.get("username")
                except:
                    pass

        return TaskOut(
            id=task_id,
            room_id=room_id,
            title=task_doc["title"],
            status=task_doc["status"],
            assignee_id=task_doc["assignee_id"],
            assignee_name=assignee_name,
            due_date=task_doc["due_date"].isoformat() if task_doc["due_date"] else None,
            created_at=task_doc["created_at"].isoformat()
        )
    
    async def get_room_tasks(self, room_id: str) -> List[TaskOut]:
        """
        Get all tasks for a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            list[TaskOut]: List of tasks
        """
        cursor = self.collection.find({"room_id": room_id}).sort("created_at", -1)
        tasks = []

        async for doc in cursor:
            assignee_name = None
            if doc.get("assignee_id"):
                if doc["assignee_id"] == "ai":
                    assignee_name = "AI"
                else:
                    # In a real app with many tasks, we would use $lookup aggregation
                    try:
                        user = await self.db.users.find_one({"_id": ObjectId(doc["assignee_id"])})
                        if user:
                            assignee_name = user.get("username")
                    except:
                        pass

            tasks.append(TaskOut(
                id=doc["id"],
                room_id=doc["room_id"],
                title=doc["title"],
                status=doc["status"],
                assignee_id=doc.get("assignee_id"),
                assignee_name=assignee_name,
                due_date=doc.get("due_date").isoformat() if doc.get("due_date") else None,
                created_at=doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else doc["created_at"]
            ))

        return tasks
    
    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Optional[TaskOut]:
        """
        Update an existing task.
        
        Args:
            task_id: Task ID
            task_data: Task update data
            
        Returns:
            Optional[TaskOut]: Updated task or None if not found
        """
        # Build update dictionary
        update_fields = {"updated_at": datetime.utcnow()}

        if task_data.title is not None:
            update_fields["title"] = task_data.title
        if task_data.status is not None:
            update_fields["status"] = task_data.status
        if task_data.assignee_id is not None:
            update_fields["assignee_id"] = task_data.assignee_id
        if task_data.due_date is not None:
            update_fields["due_date"] = task_data.due_date

        result = await self.collection.find_one_and_update(
            {"id": task_id},
            {"$set": update_fields},
            return_document=True
        )

        if not result:
            return None

        # Get assignee name
        assignee_name = None
        if result.get("assignee_id"):
            if result["assignee_id"] == "ai":
                assignee_name = "AI"
            else:
                try:
                    user = await self.db.users.find_one({"_id": ObjectId(result["assignee_id"])})
                    if user:
                        assignee_name = user.get("username")
                except:
                    pass

        return TaskOut(
            id=result["id"],
            room_id=result["room_id"],
            title=result["title"],
            status=result["status"],
            assignee_id=result.get("assignee_id"),
            assignee_name=assignee_name,
            due_date=result.get("due_date").isoformat() if result.get("due_date") else None,
            created_at=result["created_at"].isoformat() if isinstance(result["created_at"], datetime) else result["created_at"]
        )
    
    async def get_task_by_id(self, task_id: str) -> Optional[TaskOut]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Optional[TaskOut]: Task information or None
        """
        doc = await self.collection.find_one({"id": task_id})

        if not doc:
            return None

        # Get assignee name
        assignee_name = None
        if doc.get("assignee_id"):
            if doc["assignee_id"] == "ai":
                assignee_name = "AI"
            else:
                try:
                    user = await self.db.users.find_one({"_id": ObjectId(doc["assignee_id"])})
                    if user:
                        assignee_name = user.get("username")
                except:
                    pass

        return TaskOut(
            id=doc["id"],
            room_id=doc["room_id"],
            title=doc["title"],
            status=doc["status"],
            assignee_id=doc.get("assignee_id"),
            assignee_name=assignee_name,
            due_date=doc.get("due_date").isoformat() if doc.get("due_date") else None,
            created_at=doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else doc["created_at"]
        )

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task by ID.

        Args:
            task_id: Task ID

        Returns:
            bool: True if deleted
        """
        result = await self.collection.delete_one({"id": task_id})
        return result.deleted_count > 0
