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

from app.ai.gemini_client import gemini_client
from app.schemas.kb import KBUpdate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.kb_service import KBService
from app.services.message_service import MessageService
from app.services.task_service import TaskService
from motor.motor_asyncio import AsyncIOMotorDatabase

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
    service = TaskService(db)

    # Parse due_date
    parsed_date = None
    if due_date:
        try:
            parsed_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except:
            pass

    task_data = TaskCreate(
        title=title,
        assignee_id=assignee_id,
        due_date=parsed_date
    )

    result = await service.create_task(room_id, task_data)
    return result.model_dump()


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
    service = TaskService(db)

    task_data = TaskUpdate()
    if status:
        task_data.status = status
    if assignee_id:
        task_data.assignee_id = assignee_id

    result = await service.update_task(task_id, task_data)
    if not result:
        return {"error": "Task not found"}

    return result.model_dump()


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
    service = TaskService(db)
    tasks = await service.get_room_tasks(room_id)

    results = [t.model_dump() for t in tasks]

    if status:
        filtered_results = []
        for t in results:
            if t.get("status") == status:
                filtered_results.append(t)
        results = filtered_results

    return results



# Communication Tools


async def tool_translate_text(text: str, target_language: str) -> str:
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
    return await gemini_client.generate_response(prompt)


async def tool_summarize_messages(
    db: AsyncIOMotorDatabase, room_id: str, last_n: int = 20
) -> str:
    service = MessageService(db)
    messages = await service.get_recent_messages_for_context(room_id, limit=last_n)

    if not messages:
        return "No messages found to summarize."

    # Format for LLM
    message_text = ""
    for msg in messages:
        sender = msg.get("username", "Unknown")
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
    """
    service = KBService(db)

    # If adding single items, we need to fetch current state first or assume the service handles append?
    # The KBUpdate schema replaces lists. The service has 'append_key_decision'.
    # Let's use append for decisions if provided alone.

    if key_decision and not summary and not important_link:
        result = await service.append_key_decision(room_id, key_decision)
        return result.model_dump() if result else {"error": "Failed to update KB"}

    # Otherwise general update
    # We need to fetch current first to append to lists if we want to preserve them,
    # but the tool interface suggests 'add this', so appending is safer for links/decisions.

    current_kb = await service.get_room_kb(room_id)
    if not current_kb:
        # Create default
        current_kb = await service.create_default_kb(room_id)

    kb_update = KBUpdate()
    if summary:
        kb_update.summary = summary

    if key_decision:
        decisions = current_kb.key_decisions or []
        decisions.append(key_decision)
        kb_update.key_decisions = decisions

    if important_link:
        links = current_kb.important_links or []
        links.append(important_link)
        kb_update.important_links = links

    result = await service.update_kb(room_id, kb_update)
    return result.model_dump() if result else {"error": "Failed to update KB"}


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
        
    Raises:
        NotImplementedError: This feature is not yet implemented
    """
    raise NotImplementedError("Image generation is not yet implemented")


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
    """
    # TODO: Fetch user profile/style from ProfileService
    prompt = f"Rewrite the following text to match the user's style:\n\n{text}"
    return await gemini_client.generate_response(prompt)
