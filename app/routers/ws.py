"""
WebSocket router for real-time communication.
"""
import re
from typing import Dict, List, Optional

from app.db import get_database
from app.schemas.message import MessageCreate
from app.services.auth_service import AuthService
from app.services.message_service import MessageService
from app.services.room_service import RoomService
from fastapi import (APIRouter, Depends, Query, WebSocket, WebSocketDisconnect,
                     status)
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(tags=["WebSocket"])


def parse_mentions(content: str) -> List[str]:
    """
    Parse @mentions from message content.
    
    Args:
        content: Message content
        
    Returns:
        List of mentioned usernames/keywords
    """
    return re.findall(r'@(\w+)', content)


async def handle_slash_command(
    db: AsyncIOMotorDatabase,
    room_id: str,
    user_id: str,
    content: str,
    manager: "ConnectionManager"
) -> Optional[dict]:
    """
    Handle slash commands like /translate, /summarize, /search, /tasks, /help, /ask.
    
    Args:
        db: Database instance
        room_id: Room ID
        user_id: User ID
        content: Command content
        manager: Connection manager
        
    Returns:
        Command result or None if not a valid command
    """
    from app.ai.orchestrator import AIOrchestrator
    from app.services.message_service import MessageService
    
    parts = content.split(' ', 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ''
    
    orchestrator = AIOrchestrator(db)
    message_service = MessageService(db)
    
    result_content = None
    
    if command == '/help':
        result_content = """**Available Commands:**
• `/translate [lang] [text]` - Translate text to specified language
• `/summarize [n]` - Summarize the last n messages (default: 10)
• `/search [query]` - Search the web for information
• `/tasks` - List all tasks in this room
• `/ask [question]` - Ask a question about uploaded documents (RAG)
• `/docs` - List uploaded documents
• `/help` - Show this help message

**Mentions:**
• `@ai` or `@assistant` - Directly mention the AI to get a response
• `@username` - Mention a room member"""
    
    elif command == '/ask':
        # RAG document question answering
        if not args.strip():
            result_content = "**Usage:** `/ask [question]`\nExample: `/ask What are the main points in the document?`"
        else:
            from app.services.rag_service import RAGService
            rag_service = RAGService(db)
            answer = await rag_service.ask_document(room_id, args.strip())
            result_content = f"📚 **Document Q&A:**\n\n{answer}"
    
    elif command == '/docs':
        from app.services.rag_service import RAGService
        rag_service = RAGService(db)
        docs = await rag_service.get_room_documents(room_id)
        
        if not docs:
            result_content = "📁 No documents uploaded yet. Drag and drop a PDF or PowerPoint file to upload."
        else:
            doc_lines = []
            for doc in docs[:10]:
                doc_lines.append(f"• **{doc.filename}** ({doc.file_type.upper()}) - {doc.chunk_count} chunks")
            result_content = "📁 **Uploaded Documents:**\n" + "\n".join(doc_lines)
    
    elif command == '/translate':
        # Parse: /translate [lang] [text]
        translate_parts = args.split(' ', 1)
        if len(translate_parts) < 2:
            result_content = "**Usage:** `/translate [language] [text]`\nExample: `/translate spanish Hello, how are you?`"
        else:
            target_lang = translate_parts[0]
            text_to_translate = translate_parts[1]
            # Use orchestrator's translate tool
            result = await orchestrator.handle_message(
                room_id=room_id,
                user_id=user_id,
                content=f"Translate this to {target_lang}: {text_to_translate}",
                message_id="command"
            )
            result_content = result.get("content") if result else "Translation failed."
    
    elif command == '/summarize':
        # Get number of messages to summarize
        n = 10
        if args.strip().isdigit():
            n = int(args.strip())
        
        # Get recent messages
        messages = await message_service.get_room_messages(room_id=room_id, limit=n)
        if not messages:
            result_content = "No messages to summarize."
        else:
            # Format messages for summarization
            message_texts = [f"{m.sender_name or 'User'}: {m.content}" for m in reversed(messages)]
            messages_str = "\n".join(message_texts)
            
            result = await orchestrator.handle_message(
                room_id=room_id,
                user_id=user_id,
                content=f"Summarize this conversation:\n{messages_str}",
                message_id="command"
            )
            result_content = result.get("content") if result else "Summarization failed."
    
    elif command == '/search':
        if not args.strip():
            result_content = "**Usage:** `/search [query]`\nExample: `/search latest Python features`"
        else:
            result = await orchestrator.handle_message(
                room_id=room_id,
                user_id=user_id,
                content=f"Search the web for: {args}",
                message_id="command"
            )
            result_content = result.get("content") if result else "Search failed."
    
    elif command == '/tasks':
        from app.services.task_service import TaskService
        task_service = TaskService(db)
        tasks = await task_service.get_room_tasks(room_id=room_id)
        
        if not tasks:
            result_content = "📋 No tasks in this room yet."
        else:
            task_lines = []
            for t in tasks:
                status_emoji = "✅" if t.status == "done" else "⏳" if t.status == "in_progress" else "📌"
                assignee = f" ({t.assignee_name})" if t.assignee_name else ""
                task_lines.append(f"{status_emoji} **{t.title}**{assignee} - {t.status}")
            result_content = "📋 **Room Tasks:**\n" + "\n".join(task_lines)
    
    else:
        # Unknown command
        return None
    
    if result_content:
        # Save AI response to DB
        ai_message_data = MessageCreate(
            content=result_content,
            sender_type="ai"
        )
        
        ai_message = await message_service.create_message(
            room_id=room_id,
            message_data=ai_message_data,
            user_id="ai_assistant"
        )
        
        # Broadcast AI response to room
        await manager.broadcast_to_room(room_id, {
            "type": "message",
            "message": {
                "id": ai_message.id,
                "room_id": ai_message.room_id,
                "content": ai_message.content,
                "sender_type": ai_message.sender_type,
                "sender_id": "ai_assistant",
                "sender_name": "AI Assistant",
                "created_at": ai_message.created_at.isoformat() if hasattr(ai_message.created_at, 'isoformat') else str(ai_message.created_at)
            }
        })
        
        return {"handled": True}
    
    return None


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasting.
    """
    
    def __init__(self):
        """Initialize connection manager with empty connections dict."""
        # Dictionary mapping room_id to list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Mapping websocket to user_id for cleanup
        self.ws_to_user: Dict[WebSocket, str] = {}
        # Typing status per room
        self.typing_users: Dict[str, Dict[str, str]] = {}  # room_id -> {user_id: username}
        # Read receipts per room
        self.read_receipts: Dict[str, Dict[str, str]] = {}  # room_id -> {user_id: last_message_id}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            room_id: Room to join
            user_id: User ID connecting
        """
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        self.ws_to_user[websocket] = user_id
    
    async def disconnect(self, websocket: WebSocket, room_id: str) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            room_id: Room to leave
        """
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]

        user_id = self.ws_to_user.get(websocket)
        if user_id and room_id in self.typing_users:
            self.typing_users[room_id].pop(user_id, None)

        if websocket in self.ws_to_user:
            del self.ws_to_user[websocket]
    
    async def broadcast_to_room(self, room_id: str, message: dict) -> None:
        """
        Broadcast a message to all connections in a room.
        
        Args:
            room_id: Room ID
            message: Message data to broadcast
        """
        if room_id in self.active_connections:
            # Create a copy to avoid modification during iteration issues
            connections = list(self.active_connections[room_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    # If sending fails, assume disconnected and cleanup
                    await self.disconnect(connection, room_id)
    
    async def broadcast_to_user(self, user_id: str, message: dict) -> None:
        """
        Broadcast a message to a specific user across all their connections.
        
        Args:
            user_id: User ID to send to
            message: Message data to broadcast
        """
        for ws, uid in list(self.ws_to_user.items()):
            if uid == user_id:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass
    
    def get_online_users(self, room_id: str) -> List[str]:
        """Get list of online user IDs in a room."""
        if room_id not in self.active_connections:
            return []
        
        online = set()
        for ws in self.active_connections[room_id]:
            user_id = self.ws_to_user.get(ws)
            if user_id:
                online.add(user_id)
        return list(online)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> None:
    """
    WebSocket endpoint for real-time chat.
    
    Args:
        websocket: WebSocket connection
        room_id: Room ID to join
        token: Authentication token (using user_id as token for POC)
        db: Database instance
    """
    # Simple validation - in POC token is just user_id
    user_id = token
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify user exists
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Verify user is member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return

    await manager.connect(websocket, room_id, user_id)
    
    # Broadcast join message and presence update
    await manager.broadcast_to_room(room_id, {
        "type": "system",
        "content": f"{user.username} joined the chat",
        "room_id": room_id,
        "timestamp": None
    })
    
    # Send presence update with all online users
    online_users = manager.get_online_users(room_id)
    await manager.broadcast_to_room(room_id, {
        "type": "presence",
        "online_users": online_users,
        "user_joined": user_id,
        "username": user.username
    })
    
    try:
        while True:
            data = await websocket.receive_json()

            # Process message
            message_type = data.get("type")

            if message_type == "message":
                content = data.get("content")
                reply_to = data.get("reply_to")  # Message ID being replied to
                
                if content and content.strip():
                    content = content.strip()
                    
                    # Check for / commands (translate, summarize, etc.)
                    is_command = content.startswith('/')
                    command_result = None
                    
                    if is_command:
                        command_result = await handle_slash_command(
                            db, room_id, user_id, content, manager
                        )
                        if command_result:
                            # Command handled, continue to next message
                            continue
                    
                    # Save user message to DB
                    message_service = MessageService(db)
                    message_data = MessageCreate(
                        content=content,
                        sender_type="user",
                        reply_to=reply_to
                    )

                    saved_message = await message_service.create_message(
                        room_id=room_id,
                        message_data=message_data,
                        user_id=user_id
                    )

                    # Broadcast user message to room
                    await manager.broadcast_to_room(room_id, {
                        "type": "message",
                        "message": {
                            "id": saved_message.id,
                            "room_id": saved_message.room_id,
                            "content": saved_message.content,
                            "sender_type": saved_message.sender_type,
                            "sender_id": saved_message.sender_id,
                            "sender_name": saved_message.sender_name,
                            "reply_to": saved_message.reply_to,
                            "reactions": saved_message.reactions or {},
                            "created_at": saved_message.created_at.isoformat() if hasattr(saved_message.created_at, 'isoformat') else str(saved_message.created_at)
                        }
                    })
                    
                    # Check for @ mentions
                    mentions = parse_mentions(content)
                    ai_mentioned = any(m.lower() in ['ai', 'assistant', 'bot'] for m in mentions)
                    
                    # Check if replying to an AI message
                    reply_to_ai = False
                    reply_content = None
                    if reply_to:
                        replied_msg = await message_service.get_message_by_id(reply_to)
                        if replied_msg and replied_msg.sender_type == "ai":
                            reply_to_ai = True
                            reply_content = replied_msg.content
                    
                    print(f"[AI DEBUG] Message: {content[:50]}... | @mentions: {mentions} | AI mentioned: {ai_mentioned} | Reply to AI: {reply_to_ai}")
                    
                    # Check if AI should respond
                    from app.ai.classifier import ShouldRespondClassifier
                    from app.ai.orchestrator import AIOrchestrator

                    # Force AI response if explicitly mentioned or replying to AI
                    should_respond = ai_mentioned or reply_to_ai
                    
                    if not should_respond:
                        classifier = ShouldRespondClassifier()
                        orchestrator = AIOrchestrator(db)
                        
                        # Gather context for decision
                        context = await orchestrator.gather_room_context(room_id)
                        
                        # Decide if AI should respond
                        should_respond = await classifier.should_respond(
                            room_id=room_id,
                            user_id=user_id,
                            content=content,
                            context=context
                        )
                        print(f"[AI DEBUG] Classifier decision: {should_respond}")
                    else:
                        orchestrator = AIOrchestrator(db)
                        print(f"[AI DEBUG] AI mentioned directly or replied to, will respond")
                    
                    if should_respond:
                        print(f"[AI DEBUG] Getting AI response for: {content[:50]}...")
                        # Get AI response
                        ai_result = await orchestrator.handle_message(
                            room_id=room_id,
                            user_id=user_id,
                            content=content,
                            message_id=saved_message.id,
                            reply_to_content=reply_content
                        )
                        
                        print(f"[AI DEBUG] AI result: {ai_result}")
                        
                        # Broadcast tool execution results (tasks created/updated)
                        if ai_result and ai_result.get("tools_executed"):
                            for tool_result in ai_result["tools_executed"]:
                                if tool_result["type"] in ["task_created", "task_updated"]:
                                    await manager.broadcast_to_room(room_id, {
                                        "type": tool_result["type"],
                                        "task": tool_result["data"]
                                    })
                                elif tool_result["type"] == "reaction":
                                    await manager.broadcast_to_room(room_id, {
                                        "type": "reaction",
                                        "message_id": tool_result["message_id"],
                                        "emoji": tool_result["emoji"],
                                        "user": "AI Assistant"
                                    })
                        
                        if ai_result and ai_result.get("content"):
                            # Save AI response to DB
                            ai_message_data = MessageCreate(
                                content=ai_result["content"],
                                sender_type="ai",
                                reply_to=saved_message.id  # AI replies to user's message
                            )
                            
                            ai_message = await message_service.create_message(
                                room_id=room_id,
                                message_data=ai_message_data,
                                user_id="ai_assistant"  # Special AI user ID
                            )
                            
                            print(f"[AI DEBUG] Broadcasting AI response: {ai_message.content[:50]}...")
                            
                            # Broadcast AI response to room
                            await manager.broadcast_to_room(room_id, {
                                "type": "message",
                                "message": {
                                    "id": ai_message.id,
                                    "room_id": ai_message.room_id,
                                    "content": ai_message.content,
                                    "sender_type": ai_message.sender_type,
                                    "sender_id": "ai_assistant",
                                    "sender_name": "AI Assistant",
                                    "reply_to": ai_message.reply_to,
                                    "reactions": {},
                                    "created_at": ai_message.created_at.isoformat() if hasattr(ai_message.created_at, 'isoformat') else str(ai_message.created_at)
                                }
                            })
                        else:
                            print(f"[AI DEBUG] No AI response content received")
                    else:
                        print(f"[AI DEBUG] AI decided not to respond")
            
            elif message_type == "typing":
                # Broadcast typing indicator to others in room
                await manager.broadcast_to_room(room_id, {
                    "type": "typing",
                    "user_id": user_id,
                    "username": user.username,
                    "is_typing": data.get("is_typing", True)
                })
            
            elif message_type == "reaction":
                # Handle reaction to a message
                message_id = data.get("message_id")
                emoji = data.get("emoji")
                if message_id and emoji:
                    message_service = MessageService(db)
                    await message_service.add_reaction(message_id, user_id, emoji)
                    
                    # Broadcast reaction to room
                    await manager.broadcast_to_room(room_id, {
                        "type": "reaction",
                        "message_id": message_id,
                        "emoji": emoji,
                        "user": user.username
                    })
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        
        # Broadcast leave message and presence update
        await manager.broadcast_to_room(room_id, {
            "type": "system",
            "content": f"{user.username} left the chat",
            "room_id": room_id,
            "timestamp": None
        })
        
        # Send presence update with remaining online users
        online_users = manager.get_online_users(room_id)
        await manager.broadcast_to_room(room_id, {
            "type": "presence",
            "online_users": online_users,
            "user_left": user_id,
            "username": user.username
        })
    except Exception as e:
        # Log error in real app
        import logging
        logging.error(f"WebSocket error in room {room_id} for user {user_id}: {e}")
        await manager.disconnect(websocket, room_id)
