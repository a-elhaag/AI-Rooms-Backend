"""
AI tools that can be called by agents.

These tools provide concrete actions the AI can take:
- Task management
- Translation
- Summarization
- Image generation
- Web search
- KB updates
"""

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.gemini_client import gemini_client
from app.models.message import Message
from app.models.task import Task

# Task Management Tools


async def tool_create_task(
    db: AsyncIOMotorDatabase,
    room_id: str,
    title: str,
    assignee_id: Optional[str] = None,
    due_date: Optional[str] = None,
) -> dict:
    """
    Create a new task in a room.

    Args:
        db: Database instance
        room_id: Room ID
        title: Task title
        assignee_id: Optional assignee user ID or "ai"
        due_date: Optional due date (ISO format)

    Returns:
        dict: Created task information
    """
    task_data = {
        "room_id": ObjectId(room_id),
        "title": title,
        "status": "todo",
        "created_at": datetime.utcnow(),
    }

    if assignee_id:
        if assignee_id == "ai":
            task_data["assignee_id"] = "ai"
        else:
            try:
                task_data["assignee_id"] = ObjectId(assignee_id)
            except:
                pass  # Ignore invalid object ids for now

    if due_date:
        try:
            task_data["due_date"] = datetime.fromisoformat(
                due_date.replace("Z", "+00:00")
            )
        except ValueError:
            pass

    # Create task model to validate (optional but good practice)
    # task = Task(**task_data) # Skipping full validation for simplicity in tool

    result = await db["tasks"].insert_one(task_data)
    task_data["_id"] = str(result.inserted_id)
    task_data["room_id"] = str(task_data["room_id"])
    if "assignee_id" in task_data and isinstance(task_data["assignee_id"], ObjectId):
        task_data["assignee_id"] = str(task_data["assignee_id"])
    task_data["created_at"] = task_data["created_at"].isoformat()
    if "due_date" in task_data and isinstance(task_data["due_date"], datetime):
        task_data["due_date"] = task_data["due_date"].isoformat()

    return task_data


async def tool_update_task(
    db: AsyncIOMotorDatabase,
    task_id: str,
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
) -> dict:
    """
    Update an existing task.

    Args:
        db: Database instance
        task_id: Task ID
        status: Optional new status
        assignee_id: Optional new assignee

    Returns:
        dict: Updated task information
    """
    update_data = {}
    if status:
        update_data["status"] = status
    if assignee_id:
        if assignee_id == "ai":
            update_data["assignee_id"] = "ai"
        else:
            try:
                update_data["assignee_id"] = ObjectId(assignee_id)
            except:
                pass

    if not update_data:
        return {"error": "No fields to update"}

    try:
        result = await db["tasks"].find_one_and_update(
            {"_id": ObjectId(task_id)}, {"$set": update_data}, return_document=True
        )
        if result:
            result["_id"] = str(result["_id"])
            result["room_id"] = str(result["room_id"])
            if "assignee_id" in result and isinstance(result["assignee_id"], ObjectId):
                result["assignee_id"] = str(result["assignee_id"])
            return result
        return {"error": "Task not found"}
    except Exception as e:
        return {"error": str(e)}


async def tool_list_tasks(
    db: AsyncIOMotorDatabase, room_id: str, status: Optional[str] = None
) -> list[dict]:
    """
    List tasks in a room, optionally filtered by status.

    Args:
        db: Database instance
        room_id: Room ID
        status: Optional status filter

    Returns:
        list[dict]: List of tasks
    """
    query = {"room_id": ObjectId(room_id)}
    if status:
        query["status"] = status

    tasks = []
    cursor = db["tasks"].find(query).sort("created_at", -1).limit(20)
    async for task in cursor:
        task["_id"] = str(task["_id"])
        task["room_id"] = str(task["room_id"])
        if "assignee_id" in task and isinstance(task["assignee_id"], ObjectId):
            task["assignee_id"] = str(task["assignee_id"])
        task["created_at"] = task["created_at"].isoformat()
        if "due_date" in task and isinstance(task["due_date"], datetime):
            task["due_date"] = task["due_date"].isoformat()
        tasks.append(task)

    return tasks


# Communication Tools


async def tool_translate_text(text: str, target_language: str) -> str:
    """
    Translate text to target language using Google Translate or similar.

    Args:
        text: Text to translate
        target_language: Target language code (e.g., "ar", "en")

    Returns:
        str: Translated text
    """
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
    return await gemini_client.generate_response(prompt)


async def tool_summarize_messages(
    db: AsyncIOMotorDatabase, room_id: str, last_n: int = 20
) -> str:
    """
    Summarize recent messages in a room.

    Args:
        db: Database instance
        room_id: Room ID
        last_n: Number of recent messages to summarize

    Returns:
        str: Summary text
    """
    # Fetch recent messages from DB
    messages = []
    try:
        cursor = (
            db["messages"]
            .find({"room_id": ObjectId(room_id)})
            .sort("created_at", -1)
            .limit(last_n)
        )
        async for msg in cursor:
            messages.append(msg)
    except Exception:
        pass  # Handle invalid room_id gracefully

    if not messages:
        return "No messages found to summarize."

    # Reverse to chronological order
    messages.reverse()

    # Format for LLM
    message_text = ""
    for msg in messages:
        sender = (
            "AI" if msg.get("user_id") == "ai" else "User"
        )  # In real app, fetch username
        content = msg.get("content", "")
        message_text += f"{sender}: {content}\n"

    prompt = f"Summarize the following conversation:\n\n{message_text}"
    return await gemini_client.generate_response(prompt)


# Knowledge Base Tools


async def tool_update_room_kb(
    db: AsyncIOMotorDatabase,
    room_id: str,
    summary: Optional[str] = None,
    key_decision: Optional[str] = None,
    important_link: Optional[str] = None,
) -> dict:
    """
    Update room knowledge base.

    Args:
        db: Database instance
        room_id: Room ID
        summary: Optional updated summary
        key_decision: Optional key decision to add
        important_link: Optional important link to add

    Returns:
        dict: Updated KB information

    TODO:
        - Use KBService to update KB
        - Append key_decision or important_link if provided
        - Return KB data
    """
    pass


# Search and Information Tools


async def tool_web_search(query: str) -> list[dict]:
    """
    Perform web search and return results.

    Args:
        query: Search query

    Returns:
        list[dict]: Search results with title, url, snippet
    """
    # Use Gemini Grounding for search
    result_text = await gemini_client.search_web(query)

    # Return as a single result item for now, since Gemini returns synthesized text
    return [
        {"title": "Gemini Search Result", "url": "google.com", "snippet": result_text}
    ]


# Creative Tools


async def tool_generate_image(prompt: str, style: Optional[str] = None) -> str:
    """
    Generate an image using AI (placeholder for future integration).

    Args:
        prompt: Image generation prompt
        style: Optional style specification

    Returns:
        str: Image URL or base64

    TODO:
        - Integrate with image generation API (Imagen, DALL-E, etc.)
        - Return image URL
    """
    pass


# Style and Rewriting Tools


async def tool_rephrase_text(text: str, style: str = "professional") -> str:
    """
    Rephrase text in a specific style.

    Args:
        text: Text to rephrase
        style: Target style (e.g., "professional", "casual", "concise")

    Returns:
        str: Rephrased text
    """
    prompt = f"Rephrase the following text to be more {style}. Return ONLY the rephrased text without any introductory or concluding remarks, and without any formatting like markdown or quotes:\n\n{text}"
    return await gemini_client.generate_response(prompt)


async def tool_rewrite_in_user_style(
    db: AsyncIOMotorDatabase, user_id: str, text: str
) -> str:
    """
    Rewrite text in user's personal style.

    Args:
        db: Database instance
        user_id: User ID
        text: Text to rewrite

    Returns:
        str: Rewritten text

    TODO:
        - Get user profile with style notes and samples
        - Use LLM with style context to rewrite
        - Return rewritten text
    """
    pass
