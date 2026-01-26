"""
PMO Integration Helper for StrategyAgent

This module provides a non-destructive way to integrate the StrategyAgent
with existing PMO workflows. It acts as a decorator/wrapper that can be
optionally applied to PMO responses.

Usage:
    from agents.pmo_integration import validate_pmo_response, validate_pmo_response_sync
    
    # In async code:
    validated_response = await validate_pmo_response(
        pmo_draft="The PMO's proposed response",
        rag_context=["list", "of", "source", "documents"]
    )
    
    # In sync code (FastAPI handlers, etc):
    validated_response = validate_pmo_response_sync(
        pmo_draft="The PMO's proposed response",
        rag_context=["list", "of", "source", "documents"]
    )
"""

import logging
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional

from .strategy_agent import strategy_agent

logger = logging.getLogger(__name__)

_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="pmo_council")


async def validate_pmo_response(
    pmo_draft: str,
    rag_context: List[str],
    skip_validation: bool = False
) -> Dict[str, Any]:
    """
    Validate a PMO response through the StrategyAgent council.
    
    This function wraps the StrategyAgent to provide a simple interface
    for validating PMO responses before they are sent to users.
    
    Args:
        pmo_draft: The PMO's proposed response to validate
        rag_context: List of source documents from RAG retrieval
        skip_validation: If True, bypasses validation and returns draft as-is
        
    Returns:
        Dict containing:
        - validated_response: The final, hallucination-free response
        - was_modified: True if the response was changed from original
        - risk_score: 0-100 risk assessment
        - critiques: Summary of council feedback
        - original_draft: The original PMO draft for comparison
    """
    if skip_validation:
        logger.info("PMO validation skipped by request")
        return {
            "validated_response": pmo_draft,
            "was_modified": False,
            "risk_score": 50,
            "critiques": [],
            "original_draft": pmo_draft,
            "validation_skipped": True,
            "warning": "No validation performed - response passed through unreviewed"
        }
    
    try:
        logger.info("Starting StrategyAgent validation for PMO response")
        
        result = await strategy_agent.review_and_strategize(
            context_data={"rag_context": rag_context},
            proposed_draft=pmo_draft
        )
        
        if result.get("error"):
            logger.error(f"StrategyAgent error: {result.get('message')}")
            return {
                "validated_response": pmo_draft,
                "was_modified": False,
                "risk_score": 75,
                "critiques": [],
                "original_draft": pmo_draft,
                "validation_error": result.get("message")
            }
        
        strategy_eval = result.get("strategy_evaluation", {})
        final_strategy = strategy_eval.get("final_strategy", pmo_draft)
        risk_score = strategy_eval.get("risk_score", 50)
        critiques = strategy_eval.get("critiques", [])
        hallucinations_removed = strategy_eval.get("hallucinations_removed", [])
        
        was_modified = (
            final_strategy != pmo_draft or 
            len(hallucinations_removed) > 0
        )
        
        logger.info(
            f"PMO validation complete. Risk: {risk_score}, "
            f"Modified: {was_modified}, Hallucinations removed: {len(hallucinations_removed)}"
        )
        
        return {
            "validated_response": final_strategy,
            "was_modified": was_modified,
            "risk_score": risk_score,
            "critiques": critiques,
            "hallucinations_removed": hallucinations_removed,
            "consensus": strategy_eval.get("consensus", ""),
            "original_draft": pmo_draft,
            "full_evaluation": result
        }
        
    except Exception as e:
        logger.error(f"PMO validation failed: {e}")
        return {
            "validated_response": pmo_draft,
            "was_modified": False,
            "risk_score": 100,
            "critiques": [],
            "original_draft": pmo_draft,
            "validation_error": str(e)
        }


def validate_pmo_response_sync(
    pmo_draft: str,
    rag_context: List[str],
    skip_validation: bool = False
) -> Dict[str, Any]:
    """
    Synchronous wrapper for validate_pmo_response.
    
    Safe to call from sync code running inside an existing event loop
    (e.g., FastAPI handlers, sync methods called from async contexts).
    
    Uses a thread pool to run the async validation without blocking
    or conflicting with the main event loop.
    """
    def run_validation():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                validate_pmo_response(pmo_draft, rag_context, skip_validation)
            )
        finally:
            loop.close()
    
    try:
        future = _thread_pool.submit(run_validation)
        result = future.result(timeout=120)
        return result
    except concurrent.futures.TimeoutError:
        logger.error("PMO validation timed out after 120 seconds")
        return {
            "validated_response": pmo_draft,
            "was_modified": False,
            "risk_score": 75,
            "critiques": [],
            "original_draft": pmo_draft,
            "validation_error": "Validation timed out"
        }
    except Exception as e:
        logger.error(f"PMO sync validation failed: {e}")
        return {
            "validated_response": pmo_draft,
            "was_modified": False,
            "risk_score": 75,
            "critiques": [],
            "original_draft": pmo_draft,
            "validation_error": str(e)
        }


class PMOSafetyLayer:
    """
    Class-based wrapper for adding safety layer to PMO responses.
    
    Example usage:
        safety_layer = PMOSafetyLayer(enabled=True)
        
        @safety_layer.validate
        async def get_pmo_response(query: str, context: list) -> str:
            # Your existing PMO logic here
            return pmo_response
    """
    
    def __init__(self, enabled: bool = True, log_level: str = "INFO"):
        self.enabled = enabled
        self.strategy_agent = strategy_agent
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    def validate(self, func):
        """Decorator to add validation to PMO response functions."""
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            rag_context = kwargs.get('rag_context', kwargs.get('context', []))
            
            pmo_response = await func(*args, **kwargs)
            
            if not self.enabled:
                return pmo_response
            
            result = await validate_pmo_response(
                pmo_draft=pmo_response,
                rag_context=rag_context
            )
            
            return result.get("validated_response", pmo_response)
        
        return wrapper
    
    async def process(
        self, 
        pmo_draft: str, 
        rag_context: List[str]
    ) -> Dict[str, Any]:
        """Direct processing method for explicit validation calls."""
        if not self.enabled:
            return {
                "validated_response": pmo_draft,
                "was_modified": False,
                "risk_score": 50,
                "validation_skipped": True,
                "warning": "Safety layer disabled - response passed through unreviewed"
            }
        
        return await validate_pmo_response(
            pmo_draft=pmo_draft,
            rag_context=rag_context
        )


pmo_safety_layer = PMOSafetyLayer(enabled=True)
