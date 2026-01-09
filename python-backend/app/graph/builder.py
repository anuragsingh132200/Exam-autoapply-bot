"""
Graph Builder - NEW LLM-Driven Architecture
Constructs the LangGraph state machine with LLM vision decision layer.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Optional, Literal

from app.config import settings
from app.graph.state import GraphState
from app.graph.nodes import (
    init_browser_node,
    capture_screenshot_node,
    llm_decide_node,
    execute_single_action_node,
    success_node,
    save_analytics_node,
)


# Global checkpointer instance
_checkpointer: Optional[MemorySaver] = None


async def get_checkpointer() -> MemorySaver:
    """Get or create the checkpointer."""
    global _checkpointer
    
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    
    return _checkpointer


def route_after_execute(state: GraphState) -> Literal["capture_screenshot", "success", "end"]:
    """
    Route after action execution.
    If completed or failed, go to success/end.
    If waiting for input, go to END (workflow will be resumed later).
    Otherwise, loop back to capture for next action.
    """
    status = state.get("status", "running")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if status == "completed":
        return "success"
    
    if status == "waiting_input":
        # Workflow pauses here - will be resumed when user provides input
        return "end"
    
    if status == "failed" or retry_count >= max_retries:
        return "success"  # Go to success node to finalize (even for failures)
    
    # Continue the loop
    return "capture_screenshot"


def build_workflow_graph() -> StateGraph:
    """
    Build the NEW LLM-driven state machine.
    
    SIMPLIFIED Graph structure:
    START -> init_browser -> capture_screenshot -> llm_decide -> execute_action
    execute_action -> (routing) -> capture_screenshot (loop) | success | end
    success -> save_analytics -> END
    
    The key insight: LLM decides ONE action at a time, execute it, then re-capture
    and let LLM decide the next action. Simple loop until done.
    """
    
    builder = StateGraph(GraphState)
    
    # ============= Add Nodes =============
    
    builder.add_node("init_browser", init_browser_node)
    builder.add_node("capture_screenshot", capture_screenshot_node)
    builder.add_node("llm_decide", llm_decide_node)
    builder.add_node("execute_action", execute_single_action_node)
    builder.add_node("success", success_node)
    builder.add_node("save_analytics", save_analytics_node)
    
    # ============= Add Edges =============
    
    # Entry: init -> capture
    builder.add_edge(START, "init_browser")
    builder.add_edge("init_browser", "capture_screenshot")
    
    # Main loop: capture -> decide -> execute
    builder.add_edge("capture_screenshot", "llm_decide")
    builder.add_edge("llm_decide", "execute_action")
    
    # After execute: conditional routing
    builder.add_conditional_edges(
        "execute_action",
        route_after_execute,
        {
            "capture_screenshot": "capture_screenshot",  # Loop back
            "success": "success",
            "end": END,  # Pause for user input
        }
    )
    
    # Finish: success -> save -> END
    builder.add_edge("success", "save_analytics")
    builder.add_edge("save_analytics", END)
    
    return builder


async def create_compiled_graph(with_checkpointing: bool = True):
    """
    Create a compiled graph ready for execution.
    """
    builder = build_workflow_graph()
    
    if with_checkpointing:
        checkpointer = await get_checkpointer()
        
        # Compile with checkpointer
        # Note: interrupts are handled INSIDE execute_single_action_node 
        # when human input is needed (OTP, captcha)
        graph = builder.compile(
            checkpointer=checkpointer,
            # No interrupt_before - let execution proceed normally
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
    
    # Create thread config for checkpointing - increased recursion limit for long workflows
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": 100  # Increased from default 25
    }
    
    # Run the graph
    result = await graph.ainvoke(initial_state, config=config)
    
    return result


async def resume_workflow(session_id: str, user_input: any) -> dict:
    """
    Resume a paused workflow with user input.
    Gets the saved state, adds user input, clears waiting flag, and restarts.
    """
    from app.api.websocket import send_log
    
    # Get the saved state from checkpointer
    checkpointer = await get_checkpointer()
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        checkpoint = await checkpointer.aget(config)
        if not checkpoint:
            return {"success": False, "error": "No saved state found"}
        
        saved_state = checkpoint.get("values", {})
    except Exception as e:
        return {"success": False, "error": f"Failed to get state: {e}"}
    
    # Get what type of input we were waiting for
    waiting_type = saved_state.get("waiting_for_input_type")
    
    await send_log(session_id, f"✓ Received {waiting_type or 'user'} input, resuming...", "success")
    
    # Update state with user input and clear waiting flag
    updated_state = {
        **saved_state,
        "human_input_value": user_input,
        "waiting_for_input_type": None,
        "status": "running",
    }
    
    # Create graph and run from the beginning with updated state
    # Since we have checkpointing, we just re-invoke with the same thread
    graph = await create_compiled_graph()
    
    # Update config with recursion limit
    config["recursion_limit"] = 100
    
    # Re-run the workflow - it will continue from capture_screenshot
    # because the state now has status="running"
    result = await graph.ainvoke(updated_state, config=config)
    
    return result


async def get_workflow_state(session_id: str) -> Optional[dict]:
    """
    Get the current state of a workflow.
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
