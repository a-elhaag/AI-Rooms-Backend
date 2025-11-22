"""
Utility evaluator for choosing best action from candidates.
"""
from typing import Any


class UtilityEvaluator:
    """
    Evaluates candidate actions and chooses the best one based on utility.
    
    Uses a combination of heuristics and LLM reasoning to score
    different possible actions and choose the most useful one.
    """
    
    def __init__(self):
        """
        Initialize utility evaluator.
        
        TODO:
            - Load LLM for evaluation
            - Set up scoring prompts
            - Configure evaluation criteria
        """
        pass
    
    def choose_action(
        self,
        candidates: list[dict],
        context: dict
    ) -> dict:
        """
        Choose the best action from a list of candidates.
        
        Each candidate is a dict with:
        - type: "respond", "create_task", "update_kb", etc.
        - data: Action-specific data
        - reasoning: Why this action might be good
        
        Args:
            candidates: List of candidate actions
            context: Room context (goals, tasks, recent messages, etc.)
            
        Returns:
            dict: Chosen action
            
        TODO:
            - Score each candidate based on:
                - Alignment with room goals
                - Urgency/importance
                - Recency of similar actions
                - User preferences
            - Choose highest scoring action
            - Return chosen action
        """
        pass
    
    def _score_candidate(
        self,
        candidate: dict,
        context: dict
    ) -> float:
        """
        Score a single candidate action.
        
        Args:
            candidate: Candidate action
            context: Room context
            
        Returns:
            float: Utility score (0-1)
            
        TODO:
            - Calculate heuristic score
            - Optionally use LLM for complex evaluation
            - Return score
        """
        pass
    
    async def _llm_evaluate(
        self,
        candidates: list[dict],
        context: dict
    ) -> dict:
        """
        Use LLM to evaluate and choose action.
        
        Args:
            candidates: List of candidate actions
            context: Room context
            
        Returns:
            dict: Chosen action
            
        TODO:
            - Build prompt with candidates and context
            - Call LLM
            - Parse response to get chosen action
            - Return action
        """
        pass
