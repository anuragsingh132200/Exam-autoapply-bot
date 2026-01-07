"""
Graph Builder
Constructs the LangGraph state machine with MongoDBSaver checkpointing.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.config import settings
from app.graph.state import GraphState
from app.graph.nodes import (
    init_browser_node,
    capture_screenshot_node,
    analyze_page_node,
    fill_form_node,
    click_action_node,
    request_otp_node,
    request_captcha_node,
    request_custom_input_node,
    enter_input_node,
    success_node,
    error_recovery_node,
    save_analytics_node,
)
from app.graph.edges import route_after_analyze, route_after_error


# Global checkpointer instance
_checkpointer: Optional[AsyncMongoDBSaver] = None


async def get_checkpointer() -> AsyncMongoDBSaver:
    """
    Get or create the MongoDB checkpointer.
    Uses LangGraph's built-in AsyncMongoDBSaver for state persistence.
    """
    global _checkpointer
    
    if _checkpointer is None:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        _checkpointer = AsyncMongoDBSaver(client, db_name=settings.database_name)
    
    return _checkpointer


def build_workflow_graph() -> StateGraph:
    """
    Build the LangGraph state machine for workflow automation.
    
    Graph structure:
    START -> init_browser -> capture_screenshot -> analyze_page
    analyze_page -> (routing) -> fill_form | click_action | request_* | success | error
    fill_form -> capture_screenshot
    click_action -> capture_screenshot
    request_* (interrupt) -> enter_input -> capture_screenshot
    error_recovery -> capture_screenshot | END
    success -> save_analytics -> END
    """
    
    # Create graph builder with our state type
    builder = StateGraph(GraphState)
    
    # ============= Add Nodes =============
    
    builder.add_node("init_browser", init_browser_node)
    builder.add_node("capture_screenshot", capture_screenshot_node)
    builder.add_node("analyze_page", analyze_page_node)
    builder.add_node("fill_form", fill_form_node)
    builder.add_node("click_action", click_action_node)
    builder.add_node("request_otp", request_otp_node)
    builder.add_node("request_captcha", request_captcha_node)
    builder.add_node("request_custom_input", request_custom_input_node)
    builder.add_node("enter_input", enter_input_node)
    builder.add_node("success", success_node)
    builder.add_node("error_recovery", error_recovery_node)
    builder.add_node("save_analytics", save_analytics_node)
    
    # ============= Add Edges =============
    
    # Entry point
    builder.add_edge(START, "init_browser")
    
    # Main flow
    builder.add_edge("init_browser", "capture_screenshot")
    builder.add_edge("capture_screenshot", "analyze_page")
    
    # Conditional routing after analysis
    builder.add_conditional_edges(
        "analyze_page",
        route_after_analyze,
        {
            "fill_form": "fill_form",
            "click_action": "click_action",
            "request_otp": "request_otp",
            "request_captcha": "request_captcha",
            "request_custom_input": "request_custom_input",
            "success": "success",
            "error_recovery": "error_recovery",
        }
    )
    
    # After fill/click, go back to capture
    builder.add_edge("fill_form", "capture_screenshot")
    builder.add_edge("click_action", "capture_screenshot")
    
    # Human intervention nodes -> enter_input -> capture
    builder.add_edge("request_otp", "enter_input")
    builder.add_edge("request_captcha", "enter_input")
    builder.add_edge("request_custom_input", "enter_input")
    builder.add_edge("enter_input", "capture_screenshot")
    
    # Error recovery routing
    builder.add_conditional_edges(
        "error_recovery",
        route_after_error,
        {
            "capture_screenshot": "capture_screenshot",
            "success": "success",  # For failed state, go to success to finalize
        }
    )
    
    # Success path
    builder.add_edge("success", "save_analytics")
    builder.add_edge("save_analytics", END)
    
    return builder


async def create_compiled_graph(with_checkpointing: bool = True):
    """
    Create a compiled graph ready for execution.
    
    Args:
        with_checkpointing: Whether to enable MongoDB checkpointing.
                           Enable for production, disable for testing.
    
    Returns:
        Compiled LangGraph ready to run.
    """
    builder = build_workflow_graph()
    
    if with_checkpointing:
        checkpointer = await get_checkpointer()
        
        # Compile with checkpointer and interrupt configuration
        # interrupt_before specifies nodes that will pause for human input
        graph = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=["request_otp", "request_captcha", "request_custom_input"]
        )
    else:
        graph = builder.compile()
    
    return graph


async def run_workflow(
    session_id: str,
    exam_id: str,
    user_id: str,
    exam_url: str,
    exam_name: str,
    field_mappings: dict,
    user_data: dict,
) -> dict:
    """
    Run the workflow for a given session.
    
    This is the main entry point for starting a new workflow.
    """
    from app.graph.state import create_initial_state
    
    # Create initial state
    initial_state = create_initial_state(
        session_id=session_id,
        exam_id=exam_id,
        user_id=user_id,
        exam_url=exam_url,
        exam_name=exam_name,
        field_mappings=field_mappings,
        user_data=user_data,
    )
    
    # Create compiled graph
    graph = await create_compiled_graph()
    
    # Create thread config for checkpointing
    config = {"configurable": {"thread_id": session_id}}
    
    # Run the graph
    result = await graph.ainvoke(initial_state, config=config)
    
    return result


async def resume_workflow(session_id: str, user_input: dict) -> dict:
    """
    Resume a paused workflow with user input.
    
    Called after user provides OTP, captcha, or custom input.
    
    Args:
        session_id: The workflow session ID (used as thread_id)
        user_input: The user's input that was requested
    
    Returns:
        Updated state after resumption
    """
    graph = await create_compiled_graph()
    config = {"configurable": {"thread_id": session_id}}
    
    # Resume execution with the user's input
    # The input value is passed to the interrupt() call
    result = await graph.ainvoke(user_input, config=config)
    
    return result


async def get_workflow_state(session_id: str) -> Optional[dict]:
    """
    Get the current state of a workflow.
    
    Uses the checkpointer to retrieve the saved state.
    """
    checkpointer = await get_checkpointer()
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        checkpoint = await checkpointer.aget(config)
        if checkpoint:
            return checkpoint.get("values", {})
    except Exception:
        pass
    
    return None
