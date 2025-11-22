"""
Classifier to decide if AI should respond to a message.
"""
from typing import Any


class ShouldRespondClassifier:
    """
    Hybrid (LLM + rules) classifier to decide if AI should respond.
    
    Uses both rule-based heuristics and LLM judgment to determine
    if the AI should respond to a message.
    """
    
    def __init__(self):
        """
        Initialize classifier.
        
        TODO:
            - Load LLM for classification
            - Set up prompt templates
            - Configure classification thresholds
        """
        pass
    
    async def should_respond(
        self,
        room_id: str,
        user_id: str,
        content: str,
        context: dict
    ) -> bool:
        """
        Decide if AI should respond to a message.
        
        Considers:
        - Explicit mentions
        - Questions directed at AI
        - Task-related requests
        - Recent AI activity
        - Room context and goals
        
        Args:
            room_id: Room ID
            user_id: User ID
            content: Message content
            context: Room context (messages, tasks, goals, KB)
            
        Returns:
            bool: True if AI should respond
            
        TODO:
            - Check rule-based triggers (explicit mentions, keywords)
            - If unclear, call LLM classifier
            - Consider recent AI activity frequency
            - Return decision
        """
        pass
    
    def _check_rules(self, content: str) -> Optional[bool]:
        """
        Check rule-based triggers.
        
        Args:
            content: Message content
            
        Returns:
            Optional[bool]: True/False if rule matches, None if unclear
            
        TODO:
            - Check for @AI mentions
            - Check for question words directed at AI
            - Check for task keywords
            - Return decision or None
        """
        pass
    
    async def _llm_classify(
        self,
        content: str,
        context: dict
    ) -> bool:
        """
        Use LLM to classify if AI should respond.
        
        Args:
            content: Message content
            context: Room context
            
        Returns:
            bool: True if AI should respond
            
        TODO:
            - Build prompt with context
            - Call LLM
            - Parse response (yes/no)
            - Return decision
        """
        pass
