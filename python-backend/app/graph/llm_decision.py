"""
LLM Vision Decision Module

Uses Gemini Vision to analyze screenshots and decide the next action.
Returns structured outputs that map directly to Stagehand actions.
"""
import base64
import json
from typing import Optional, Literal
from pydantic import BaseModel, Field
import google.generativeai as genai

from app.config import settings


# Configure Gemini
genai.configure(api_key=settings.google_api_key)


# ==================== Structured Output Schemas ====================

class ActionDecision(BaseModel):
    """Structured output from LLM decision."""
    
    action_type: Literal[
        "click_checkbox",
        "fill_field", 
        "click_button",
        "wait_for_human",
        "success",
        "error",
        "retry"
    ] = Field(description="Type of action to perform")
    
    # For click_checkbox
    checkbox_label: Optional[str] = Field(
        default=None,
        description="Label/text of checkbox to click (e.g., 'I hereby declare...')"
    )
    
    # For fill_field
    field_name: Optional[str] = Field(
        default=None,
        description="Name of the field to fill (e.g., 'full name', 'email address')"
    )
    field_value: Optional[str] = Field(
        default=None, 
        description="Value to fill in the field"
    )
    
    # For click_button
    button_text: Optional[str] = Field(
        default=None,
        description="Text of button to click (e.g., 'Submit', 'Continue', 'Next')"
    )
    
    # For wait_for_human
    wait_reason: Optional[str] = Field(
        default=None,
        description="Why human input is needed (e.g., 'OTP required', 'Captcha detected')"
    )
    input_type: Optional[Literal["otp", "captcha", "custom"]] = Field(
        default=None,
        description="Type of human input needed"
    )
    
    # For error/retry
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if action_type is error"
    )
    
    # The actual prompt to send to Stagehand
    stagehand_prompt: str = Field(
        description="The exact natural language prompt to send to Stagehand's act() function"
    )
    
    reasoning: str = Field(
        description="Brief explanation of why this action was chosen"
    )


# ==================== System Prompt ====================

SYSTEM_PROMPT = """You are an expert form automation assistant. You analyze screenshots of web pages and decide the SINGLE BEST ACTION to take next.

## Your Role
1. Analyze the screenshot to understand the current page state
2. Consider what user data still needs to be filled
3. Decide ONE specific action to take
4. Generate a precise Stagehand prompt for that action

## CRITICAL RULES (Follow in STRICT order)

### 1. POPUP/DIALOG HANDLING (Check FIRST!)
If you see ANY popup, modal, or dialog box on the screen:
- If it has an "OK", "Close", "Continue", or "X" button → CLICK it to dismiss
- Example: "Success - OTP has been sent" popup → Click "OK" button
- Return action_type: "click_button" with the button text

### 2. OTP INPUT DETECTION (ONLY OTP needs human!)
TRIGGER wait_for_human if you see ANY of these:
- Empty OTP input boxes (usually 4-6 separate boxes for digits)
- Text containing: "Enter OTP", "Enter verification code", "OTP sent to", "Verify mobile otp", "Verify phone otp", "Mobile verification", "SMS verification"
- A "Verify" or "Verify Mobile" or "Verify Phone" or "Verify OTP" button
- An input field specifically labeled "OTP" or "Enter OTP"
- A page asking to verify email OR mobile with OTP

⚠️ IMPORTANT: If you see "Enter OTP" or "OTP" or "verification code" anywhere:
- DO NOT try to fill this with user data like phone number!
- The user must manually enter the OTP they received
- Return action_type: "wait_for_human" with input_type: "otp"
- stagehand_prompt should be empty for wait_for_human
- wait_reason should describe what OTP is needed (e.g., "Mobile OTP verification required")

### 3. CAPTCHA SOLVING (YOU solve it - no human needed!)
If you see a captcha image:
- READ the captcha text from the image carefully
- Pay attention to case sensitivity (uppercase vs lowercase letters)
- Type EXACTLY what you see, with no extra spaces
- Return action_type: "fill_field" with:
  - field_name: "captcha"
  - field_value: exactly what you read from the captcha image
  - stagehand_prompt: "Find the captcha input field and type '[your captcha reading]' into it"
DO NOT return wait_for_human for captcha - solve it yourself!

### 4. CHECKBOX HANDLING
If there's an UNCHECKED checkbox (like "I hereby declare...", terms), CLICK IT

### 5. FORM FIELD FILLING - CHECK CAREFULLY!
BEFORE clicking submit, carefully scan the ENTIRE page for ANY empty input fields:
- Look for empty text boxes, empty input fields, empty captcha fields
- If you see an EMPTY captcha input field (no text in it), fill it FIRST by reading the captcha image
- An empty captcha field means the previous captcha was WRONG - solve it again!
- Fill unfilled fields ONE AT A TIME

⚠️ CRITICAL: If a captcha field is visible and EMPTY:
- The captcha was likely wrong last time
- DO NOT click submit!
- READ the captcha image and FILL the captcha field first

### 6. SUBMIT BUTTON - ONLY if ALL fields are FILLED!
BEFORE clicking Submit/Get OTP/Continue:
- Double-check that the captcha field has text in it
- Double-check all required fields are filled
- If ANY field is empty, fill it first instead of clicking submit!

### 7. SUCCESS DETECTION - BE VERY CAREFUL
ONLY return "success" if you see FINAL confirmation like:
- "Registration successful"
- "Application submitted successfully" 
- "Your registration is complete"

DO NOT confuse these with success:
- "OTP sent successfully" → This is NOT final success, it means wait for OTP
- "Captcha verified" → This is NOT final success
- Just clicking something → NOT success
- Error messages like "Invalid captcha" → Need to re-solve captcha!

## Stagehand Prompt Guidelines
- For click_button: "Click the 'OK' button" or "Click the 'Submit' button"
- For fill_field: "Find the email field and type 'test@email.com'"
- For wait_for_human: stagehand_prompt can be empty or describe what's needed
- For click_checkbox: "Click the checkbox next to 'I hereby declare...'"

## Output Format
Return a JSON object with:
- action_type: One of "click_checkbox", "fill_field", "click_button", "wait_for_human", "success", "error", "retry"
- For wait_for_human: include input_type ("otp" or "captcha") and wait_reason
- stagehand_prompt: The exact prompt for Stagehand (empty for wait_for_human)
- reasoning: Brief explanation"""


# ==================== Decision Function ====================

async def decide_next_action(
    screenshot_base64: str,
    user_data: dict,
    already_filled: list[str],
    page_url: str = "",
    retry_count: int = 0,
    captcha_fail_count: int = 0
) -> ActionDecision:
    """
    Analyze screenshot and decide the next action.
    
    Args:
        screenshot_base64: Base64 encoded screenshot
        user_data: Dictionary of user data to fill (e.g., {"name": "John", "email": "john@test.com"})
        already_filled: List of field keys that have already been filled
        page_url: Current page URL for context
        retry_count: Number of retries so far
        captcha_fail_count: Number of failed captcha attempts (fallback to human after 3)
    
    Returns:
        ActionDecision with the next action to take
    """
    
    # Build the user context
    remaining_fields = {k: v for k, v in user_data.items() if k not in already_filled and v}
    
    # If captcha has failed 3 times, force human input
    captcha_note = ""
    if captcha_fail_count >= 3:
        captcha_note = "\n\n CAPTCHA AUTO-SOLVE HAS FAILED 3 TIMES. If you see a captcha, return wait_for_human with input_type='captcha' to ask the user to solve it."
    
    # Check if captcha was already filled
    captcha_filled_note = ""
    if "captcha" in already_filled:
        captcha_filled_note = "\n\n✅ CAPTCHA WAS ALREADY FILLED - DO NOT FILL IT AGAIN! Even if the field looks empty, you already filled it. Move on to clicking the submit button!"
    
    user_context = f"""
## User Data to Fill
Already filled: {already_filled if already_filled else "None yet"}
Remaining to fill: {json.dumps(remaining_fields, indent=2)}{captcha_filled_note}

## Current State  
Page URL: {page_url or "Unknown"}
Retry count: {retry_count}
Captcha failures: {captcha_fail_count}{captcha_note}

## CRITICAL RULE
If a field is in "Already filled" list above, DO NOT try to fill it again!
If "captcha" is in Already filled, click the submit button instead of filling captcha again.

## Task
Analyze the screenshot and decide the SINGLE next action to take.
If there's an unchecked checkbox visible, click it first.
If there are form fields, fill the next unfilled one from the remaining fields.
If all fields are filled (including captcha in Already filled list), click the submit button.
"""

    try:
        # Initialize Gemini model with vision capability
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "response_mime_type": "application/json",
            }
        )
        
        # Decode image for Gemini
        image_data = base64.b64decode(screenshot_base64)
        
        # Create the prompt
        prompt_parts = [
            SYSTEM_PROMPT,
            user_context,
            {"mime_type": "image/png", "data": image_data}
        ]
        
        print(f"[LLM] Calling Gemini Vision with {len(image_data)} bytes image...")
        
        # Generate response with timeout
        import asyncio
        try:
            # Run sync call in executor with timeout
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: model.generate_content(prompt_parts)),
                timeout=60.0  # 60 second timeout
            )
        except asyncio.TimeoutError:
            print("[LLM] Gemini API call timed out after 60s")
            return ActionDecision(
                action_type="retry",
                stagehand_prompt="",
                reasoning="LLM analysis timed out - retrying",
                error_message="Timeout"
            )
        
        response_text = response.text.strip()
        print(f"[LLM] Got response: {response_text[:200]}...")
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            return ActionDecision(**result)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                return ActionDecision(**result)
            raise
            
    except Exception as e:
        print(f"[LLM] Error: {e}")
        # Return a retry action on error
        return ActionDecision(
            action_type="retry",
            stagehand_prompt="",
            reasoning=f"Failed to analyze page: {str(e)}",
            error_message=str(e)
        )


# ==================== Action Execution Helpers ====================

def build_fill_prompt(field_name: str, value: str) -> str:
    """Build a specific fill prompt based on field type."""
    field_lower = field_name.lower()
    
    # Handle confirm/re-enter fields
    if "confirm" in field_lower or "re-enter" in field_lower or "retype" in field_lower:
        return f"Find the confirmation/re-enter field for {field_name.replace('confirm', '').strip()} and type '{value}' into it"
    
    # Handle specific field types
    if "email" in field_lower:
        return f"Find the email input field and type '{value}' into it. Clear any existing text first."
    
    if "phone" in field_lower or "mobile" in field_lower:
        return f"Find the phone/mobile number input field and type '{value}' into it"
    
    if "date" in field_lower or "dob" in field_lower:
        return f"Find the date of birth field and enter '{value}'"
    
    # Default
    return f"Find the input field labeled '{field_name}' or with placeholder '{field_name}' and type '{value}' into it. Clear existing text first."


def build_checkbox_prompt(label: str) -> str:
    """Build a checkbox click prompt."""
    # Truncate long labels
    short_label = label[:100] + "..." if len(label) > 100 else label
    return f"Find and click the unchecked checkbox associated with the text: '{short_label}'"


def build_button_prompt(button_text: str) -> str:
    """Build a button click prompt."""
    return f"Click the button labeled '{button_text}'. Look for buttons, links, or submit elements."
