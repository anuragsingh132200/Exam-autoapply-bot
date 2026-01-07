"""
Graph Edges (Routing Logic)
Conditional routing functions for LangGraph.
"""
from typing import Literal
from app.graph.state import GraphState


def route_after_analyze(state: GraphState) -> Literal[
    "fill_form",
    "click_action",
    "request_otp",
    "request_captcha",
    "request_custom_input",
    "success",
    "error_recovery"
]:
    """
    Route based on page analysis results.
    This is the main routing function that decides the next action.
    """
    analysis = state.get("analysis", {})
    
    if not analysis:
        return "error_recovery"
    
    next_action = analysis.get("next_action", "retry")
    page_type = analysis.get("page_type", "unknown")
    
    # Check for success/error first
    if next_action == "success" or page_type == "success":
        return "success"
    
    if next_action == "error" or page_type == "error":
        return "error_recovery"
    
    # Route based on next_action
    if next_action == "fill_form":
        return "fill_form"
    
    if next_action == "click_submit":
        return "click_action"
    
    if next_action == "request_otp" or analysis.get("has_otp_field"):
        return "request_otp"
    
    if next_action == "request_captcha" or analysis.get("has_captcha"):
        return "request_captcha"
    
    if next_action == "request_custom_input":
        return "request_custom_input"
    
    if next_action == "wait":
        # If waiting, go back to capture to check again
        return "fill_form"
    
    if next_action == "retry":
        return "error_recovery"
    
    # Default: try to fill form
    return "fill_form"


def route_after_error(state: GraphState) -> Literal["capture_screenshot", "success"]:
    """
    Route after error recovery.
    Either retry (back to capture) or give up.
    """
    status = state.get("status", "running")
    
    if status == "failed":
        return "success"  # Actually goes to end, but we use success node to finalize
    
    # Retry - go back to capture
    return "capture_screenshot"


def should_continue_workflow(state: GraphState) -> bool:
    """
    Check if workflow should continue or stop.
    """
    status = state.get("status", "running")
    
    if status in ["success", "failed"]:
        return False
    
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if retry_count >= max_retries:
        return False
    
    return True
