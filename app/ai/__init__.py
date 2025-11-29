"""
AI package containing the separated LLM architecture.

Architecture:
- ai_coordinator.py: Main entry point, orchestrates tool execution and response generation
- tool_executor.py: Silent LLM that only triggers tools (tasks, reactions, searches)
- chat_responder.py: LLM that only generates user-facing text responses
- classifier.py: Decides if AI should respond to a message
- gemini_client.py: Wrapper for Google Gemini API
- tools.py: Tool implementations (task management, search, etc.)
- orchestrator.py: [DEPRECATED] Legacy combined LLM - use ai_coordinator instead
"""
