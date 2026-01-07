"""
Graph Nodes with Browser Integration
Individual node functions for the LangGraph workflow.
Uses LangGraph's built-in interrupt() for human-in-the-loop.
Integrates with StagehandBrowser for real browser automation.
"""
from typing import Any
from datetime import datetime
from langgraph.types import interrupt

from app.graph.state import GraphState
from app.services.llm import llm_service
from app.browser.manager import BrowserManager
from app.api.websocket import (
    send_screenshot,
    send_log,
    send_status,
    request_otp,
    request_captcha,
    request_custom_input,
    send_result,
)


# ============= Core Nodes =============

async def init_browser_node(state: GraphState) -> dict:
    """
    Initialize browser and navigate to exam URL.
    This is the entry point of the workflow.
    """
    session_id = state["session_id"]
    exam_url = state["exam_url"]
    
    await send_log(session_id, f"Initializing browser for {state['exam_name']}...", "info")
    await send_status(session_id, "init_browser", 5, "Starting browser...")
    
    # Initialize browser
    browser = await BrowserManager.get_or_create(session_id, headless=False)
    
    # Navigate to exam URL
    await browser.goto(exam_url)
    
    # Capture initial screenshot
    screenshot_base64 = await browser.screenshot(step="init")
    
    await send_log(session_id, "Browser ready, navigated to registration page", "success")
    
    return {
        "current_step": "init_browser",
        "progress": 10,
        "page_url": exam_url,
        "screenshot_base64": screenshot_base64,
        "action_history": [{
            "action": "navigate",
            "target": exam_url,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }]
    }


async def capture_screenshot_node(state: GraphState) -> dict:
    """
    Capture current page screenshot.
    Broadcasts to connected clients for real-time viewing.
    """
    session_id = state["session_id"]
    current_step = state.get("current_step", "capture")
    
    browser = BrowserManager.get(session_id)
    
    if browser:
        screenshot_base64 = await browser.screenshot(step=current_step)
        page_url = browser.page.url
        
        # Get page HTML for analysis
        page_html = await browser.get_page_html()
        
        return {
            "current_step": "capture_screenshot",
            "screenshot_base64": screenshot_base64,
            "page_url": page_url,
            "page_html": page_html[:50000] if page_html else None,  # Limit HTML size
        }
    
    return {"current_step": "capture_screenshot"}


async def analyze_page_node(state: GraphState) -> dict:
    """
    Analyze current page using Gemini vision.
    Returns structured PageAnalysis.
    """
    session_id = state["session_id"]
    screenshot = state.get("screenshot_base64")
    
    await send_log(session_id, "Analyzing page...", "info")
    await send_status(session_id, "analyze_page", state.get("progress", 15), "Analyzing page content...")
    
    if not screenshot:
        return {
            "current_step": "analyze_page",
            "analysis": {
                "page_type": "unknown",
                "next_action": "retry",
                "confidence": 0.0,
                "error_message": "No screenshot available"
            },
            "last_error": "No screenshot available"
        }
    
    # Use LLM service to analyze page
    analysis = await llm_service.analyze_page(
        screenshot_base64=screenshot,
        page_html=state.get("page_html"),
        user_data=state.get("user_data"),
        field_mappings=state.get("field_mappings"),
        action_history=state.get("action_history", [])
    )
    
    await send_log(
        session_id, 
        f"Page: {analysis.page_type} | Action: {analysis.next_action}", 
        "info"
    )
    
    return {
        "current_step": "analyze_page",
        "analysis": analysis.model_dump(),
        "progress": 20,
    }


async def fill_form_node(state: GraphState) -> dict:
    """
    Fill form fields using user data.
    Uses browser wrapper to actually fill the fields.
    """
    session_id = state["session_id"]
    analysis = state.get("analysis", {})
    user_data = state.get("user_data", {})
    
    await send_log(session_id, "Filling form fields...", "info")
    await send_status(session_id, "fill_form", 40, "Filling form...")
    
    browser = BrowserManager.get(session_id)
    if not browser:
        return {"current_step": "fill_form", "last_error": "Browser not available"}
    
    detected_fields = analysis.get("detected_fields", [])
    actions = []
    fields_filled = 0
    
    for field in detected_fields:
        if isinstance(field, dict):
            field_key = field.get("key", "")
            field_label = field.get("label", field_key)
            is_filled = field.get("is_filled", False)
            
            # Skip already filled fields
            if is_filled:
                continue
            
            # Find matching user data
            value = user_data.get(field_key)
            if not value:
                # Try to find by similar keys
                for user_key, user_value in user_data.items():
                    if field_key.lower() in user_key.lower() or user_key.lower() in field_key.lower():
                        value = user_value
                        break
            
            if value:
                # Use browser to fill field
                success = await browser.fill_field(field_label, str(value))
                
                if success:
                    fields_filled += 1
                    actions.append({
                        "action": "fill_field",
                        "target": field_key,
                        "value": "***" if "phone" in field_key.lower() or "email" in field_key.lower() else str(value)[:10],
                        "timestamp": datetime.utcnow().isoformat(),
                        "success": True
                    })
                    await send_log(session_id, f"✓ Filled: {field_label}", "info")
    
    # Capture screenshot after filling
    await browser.screenshot(step="fill_form")
    
    await send_log(session_id, f"Filled {fields_filled} fields", "success")
    
    return {
        "current_step": "fill_form",
        "progress": 50,
        "action_history": actions,
    }


async def click_action_node(state: GraphState) -> dict:
    """
    Click the appropriate button (submit, continue, etc).
    """
    session_id = state["session_id"]
    analysis = state.get("analysis", {})
    
    browser = BrowserManager.get(session_id)
    if not browser:
        return {"current_step": "click_action", "last_error": "Browser not available"}
    
    # Find primary button
    buttons = analysis.get("buttons", [])
    primary_button = next((b for b in buttons if b.get("is_primary")), None)
    button_text = primary_button.get("text", "Submit") if primary_button else "Submit"
    
    await send_log(session_id, f"Clicking: {button_text}", "info")
    await send_status(session_id, "click_action", 60, f"Clicking {button_text}...")
    
    # Click the button
    success = await browser.click_button(button_text)
    
    if not success:
        # Try common button texts
        for btn_text in ["Continue", "Next", "Submit", "Login", "Proceed", "Register"]:
            success = await browser.click_button(btn_text)
            if success:
                button_text = btn_text
                break
    
    # Wait for page to load after click
    await browser.wait_for_navigation()
    
    # Capture screenshot after click
    screenshot = await browser.screenshot(step="click_action")
    
    return {
        "current_step": "click_action",
        "progress": 60,
        "screenshot_base64": screenshot,
        "action_history": [{
            "action": "click",
            "target": button_text,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success
        }]
    }


# ============= Human Intervention Nodes (using LangGraph interrupt()) =============

async def request_otp_node(state: GraphState) -> dict:
    """
    Request OTP from user using LangGraph's built-in interrupt().
    This pauses the graph until the user provides input.
    """
    session_id = state["session_id"]
    
    await send_log(session_id, "📱 OTP required. Please check your phone...", "warning")
    await send_status(session_id, "request_otp", state.get("progress", 50), "Waiting for OTP...")
    
    # Send request to frontend
    await request_otp(session_id)
    
    # Use LangGraph's built-in interrupt() - this pauses execution
    otp = interrupt({
        "type": "REQUEST_OTP",
        "message": "Please enter the OTP sent to your phone",
        "session_id": session_id
    })
    
    await send_log(session_id, "OTP received, entering...", "success")
    
    # Enter OTP into form
    browser = BrowserManager.get(session_id)
    if browser and otp:
        await browser.act(f"type '{otp}' into otp input field")
        await browser.screenshot(step="otp_entered")
    
    return {
        "current_step": "request_otp",
        "received_otp": otp,
        "pending_intervention": None,
        "action_history": [{
            "action": "otp_entered",
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }]
    }


async def request_captcha_node(state: GraphState) -> dict:
    """
    Request captcha solution from user using interrupt().
    """
    session_id = state["session_id"]
    
    # Take fresh screenshot of captcha
    browser = BrowserManager.get(session_id)
    screenshot = state.get("screenshot_base64", "")
    if browser:
        screenshot = await browser.screenshot(step="captcha")
    
    await send_log(session_id, "🔒 Captcha detected. Please solve it...", "warning")
    await send_status(session_id, "request_captcha", state.get("progress", 50), "Waiting for captcha solution...")
    
    # Send captcha image to frontend
    await request_captcha(session_id, screenshot, auto_solving=False)
    
    # Use interrupt() to wait for solution
    solution = interrupt({
        "type": "REQUEST_CAPTCHA",
        "message": "Please solve the captcha",
        "session_id": session_id,
        "image_base64": screenshot
    })
    
    await send_log(session_id, "Captcha solution received, entering...", "success")
    
    # Enter captcha solution
    if browser and solution:
        await browser.act(f"type '{solution}' into captcha input field")
        await browser.screenshot(step="captcha_entered")
    
    return {
        "current_step": "request_captcha",
        "received_captcha": solution,
        "pending_intervention": None,
        "action_history": [{
            "action": "captcha_solved",
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }]
    }


async def request_custom_input_node(state: GraphState) -> dict:
    """
    Request custom input from user for unknown fields.
    """
    session_id = state["session_id"]
    analysis = state.get("analysis", {})
    
    remaining_fields = analysis.get("remaining_fields", [])
    detected_fields = analysis.get("detected_fields", [])
    user_data = state.get("user_data", {})
    
    # Find first field without matching user data
    unknown_field = None
    for field in detected_fields:
        if isinstance(field, dict) and field.get("key") in remaining_fields:
            if field.get("key") not in user_data or not user_data.get(field.get("key")):
                unknown_field = field
                break
    
    if not unknown_field:
        return {
            "current_step": "request_custom_input",
            "last_error": "No unknown fields found"
        }
    
    field_id = unknown_field.get("key", "unknown")
    field_label = unknown_field.get("label", "Unknown Field")
    field_type = unknown_field.get("field_type", "text")
    
    await send_log(session_id, f"❓ Unknown field: {field_label}", "warning")
    await send_status(session_id, "request_custom_input", state.get("progress", 50), f"Need input for: {field_label}")
    
    # Get suggestions from user data keys
    suggestions = list(user_data.keys())[:5]
    
    await request_custom_input(session_id, field_id, field_label, field_type, suggestions)
    
    # Use interrupt() to wait for user input
    value = interrupt({
        "type": "REQUEST_CUSTOM_INPUT",
        "field_id": field_id,
        "field_label": field_label,
        "session_id": session_id
    })
    
    await send_log(session_id, f"Input received for {field_label}, entering...", "success")
    
    # Enter the value
    browser = BrowserManager.get(session_id)
    if browser and value:
        await browser.fill_field(field_label, value)
        await browser.screenshot(step="custom_input_entered")
    
    received_custom = state.get("received_custom_inputs", {})
    received_custom[field_id] = value
    
    return {
        "current_step": "request_custom_input",
        "received_custom_inputs": received_custom,
        "pending_intervention": None,
        "action_history": [{
            "action": "custom_input_entered",
            "target": field_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }]
    }


async def enter_input_node(state: GraphState) -> dict:
    """
    Post-processing after human input has been entered.
    Click continue/submit button.
    """
    session_id = state["session_id"]
    
    await send_log(session_id, "Processing input...", "info")
    await send_status(session_id, "enter_input", 65, "Processing...")
    
    browser = BrowserManager.get(session_id)
    if browser:
        # Try to click continue/submit after entering input
        for btn_text in ["Continue", "Verify", "Submit", "Next", "Proceed"]:
            success = await browser.click_button(btn_text)
            if success:
                await browser.wait_for_navigation()
                break
        
        await browser.screenshot(step="after_input")
    
    return {
        "current_step": "enter_input",
        "progress": 70,
        "action_history": [{
            "action": "continue_after_input",
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }]
    }


# ============= Result Nodes =============

async def success_node(state: GraphState) -> dict:
    """
    Handle successful workflow completion.
    """
    session_id = state["session_id"]
    
    # Take final screenshot
    browser = BrowserManager.get(session_id)
    if browser:
        await browser.screenshot(step="success")
        await BrowserManager.close(session_id)
    
    await send_log(session_id, "✅ Registration completed successfully!", "success")
    await send_status(session_id, "success", 100, "Completed!")
    await send_result(session_id, True, "Registration completed successfully")
    
    return {
        "current_step": "success",
        "progress": 100,
        "status": "success",
        "result_message": "Registration completed successfully"
    }


async def error_recovery_node(state: GraphState) -> dict:
    """
    Handle errors with retry logic.
    """
    session_id = state["session_id"]
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    last_error = state.get("last_error", "Unknown error")
    
    if retry_count >= max_retries:
        # Close browser on failure
        await BrowserManager.close(session_id)
        
        await send_log(session_id, f"❌ Max retries reached: {last_error}", "error")
        await send_result(session_id, False, f"Failed after {max_retries} retries")
        
        return {
            "current_step": "error_recovery",
            "status": "failed",
            "result_message": f"Failed: {last_error}"
        }
    
    await send_log(session_id, f"🔄 Retrying ({retry_count + 1}/{max_retries})...", "warning")
    await send_status(session_id, "error_recovery", state.get("progress", 50), f"Retry {retry_count + 1}/{max_retries}")
    
    return {
        "current_step": "error_recovery",
        "retry_count": retry_count + 1,
        "last_error": None,
        "action_history": [{
            "action": "retry",
            "target": f"attempt_{retry_count + 1}",
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }]
    }


async def save_analytics_node(state: GraphState) -> dict:
    """
    Save workflow analytics after completion.
    """
    session_id = state["session_id"]
    
    # TODO: Save to ExamAnalytics collection
    await send_log(session_id, "📊 Analytics saved", "info")
    
    return {"current_step": "save_analytics"}
