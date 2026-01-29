"""
Centralized project serialization for frontend consistency.
This module ensures all API endpoints return projects in a consistent format
that matches what the frontend expects.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List


def flatten_project_for_frontend(
    defense_file: Dict[str, Any],
    include_deliberations: bool = False
) -> Dict[str, Any]:
    """
    Flatten a defense file into a project structure that the frontend expects.
    
    The frontend expects these fields directly on the project object:
    - project_id
    - project_name
    - sponsor_name
    - sponsor_email
    - company_name
    - description
    - budget_estimate (not 'amount')
    - expected_benefit
    - status
    - workflow_state
    - deliberation_count
    - compliance_score
    - created_at
    - final_decision
    
    Args:
        defense_file: The raw defense file from storage
        include_deliberations: Whether to include full deliberation details
        
    Returns:
        Flattened project dictionary matching frontend expectations
    """
    if not defense_file:
        return {}
    
    project_data = defense_file.get("project_data", {})
    deliberations = defense_file.get("deliberations", [])
    last_delib = deliberations[-1] if deliberations else {}
    
    final_decision = defense_file.get("final_decision", "")
    if final_decision == "approve":
        status = "approved"
    elif final_decision in ["reject", "rejected"]:
        status = "rejected"
    else:
        status = "in_review"
    
    flattened = {
        "project_id": defense_file.get("project_id", ""),
        "project_name": project_data.get("name", "Sin nombre"),
        "sponsor_name": project_data.get("sponsor_name", ""),
        "sponsor_email": project_data.get("sponsor_email", ""),
        "company_name": project_data.get("client_name", ""),
        "description": project_data.get("description", ""),
        "budget_estimate": project_data.get("amount", 0) or 0,
        "budget": project_data.get("amount", 0) or 0,
        "expected_benefit": project_data.get("expected_benefit", 0) or 0,
        "department": project_data.get("department", ""),
        "duration_months": project_data.get("duration_months", 12),
        "urgency_level": project_data.get("urgency_level", "Normal"),
        "service_type": project_data.get("service_type", ""),
        "status": status,
        "current_status": status,
        "workflow_state": last_delib.get("stage", "E1_ESTRATEGIA"),
        "created_at": defense_file.get("created_at"),
        "compliance_score": defense_file.get("compliance_score", 0) or 0,
        "final_decision": final_decision,
        "final_justification": defense_file.get("final_justification", ""),
        "deliberation_count": len(deliberations),
        "is_modification": project_data.get("is_modification", False),
        "parent_folio": project_data.get("parent_folio", ""),
        "attachments": project_data.get("attachments", [])
    }
    
    if include_deliberations:
        flattened["deliberations"] = deliberations
    
    return flattened


def flatten_project_for_list(
    defense_file: Dict[str, Any],
    full_defense_file: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Flatten a defense file for list views (lighter version).
    
    Args:
        defense_file: The defense file summary from list_all()
        full_defense_file: Optional full defense file for additional data
        
    Returns:
        Flattened project for list display
    """
    if full_defense_file:
        project_data = full_defense_file.get("project_data", {})
        deliberations = full_defense_file.get("deliberations", [])
        last_delib = deliberations[-1] if deliberations else {}
    else:
        project_data = defense_file.get("project_data", {})
        deliberations = []
        last_delib = {}
    
    final_decision = defense_file.get("final_decision", "")
    if final_decision == "approve":
        status = "approved"
    elif final_decision in ["reject", "rejected"]:
        status = "rejected"
    else:
        status = "in_review"
    
    created_at = defense_file.get("created_at")
    days_elapsed = 0
    if created_at:
        try:
            if isinstance(created_at, str):
                from dateutil import parser
                created_dt = parser.parse(created_at)
            else:
                created_dt = created_at
            days_elapsed = (datetime.now(created_dt.tzinfo) - created_dt).days
        except (ValueError, TypeError, AttributeError):
            pass  # Invalid date format, default to 0 days
    
    return {
        "project_id": defense_file.get("project_id", ""),
        "project_name": project_data.get("name", "Sin nombre"),
        "sponsor_name": project_data.get("sponsor_name", ""),
        "sponsor_email": project_data.get("sponsor_email", ""),
        "company_name": project_data.get("client_name", ""),
        "description": project_data.get("description", ""),
        "budget_estimate": project_data.get("amount", 0) or 0,
        "budget": project_data.get("amount", 0) or 0,
        "expected_benefit": project_data.get("expected_benefit", 0) or 0,
        "status": status,
        "current_status": status,
        "workflow_state": last_delib.get("stage", "E1_ESTRATEGIA"),
        "days_elapsed": days_elapsed,
        "last_feedback_days": days_elapsed,
        "created_at": created_at,
        "compliance_score": defense_file.get("compliance_score", 0) or 0,
        "deliberation_count": full_defense_file.get("deliberation_count", 0) if full_defense_file else 0,
        "final_decision": final_decision
    }


def get_project_amount(defense_file: Dict[str, Any]) -> float:
    """
    Safely extract the project amount from a defense file.
    Handles various field names (amount, budget_estimate, etc.)
    
    Args:
        defense_file: The defense file
        
    Returns:
        The project amount as a float
    """
    project_data = defense_file.get("project_data", {})
    
    amount = project_data.get("amount")
    if amount is not None:
        try:
            return float(amount)
        except (ValueError, TypeError):
            pass
    
    budget = project_data.get("budget_estimate")
    if budget is not None:
        try:
            return float(budget)
        except (ValueError, TypeError):
            pass
    
    return 0.0
