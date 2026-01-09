"""
GraphState Definition
Defines the state that flows through the LangGraph workflow.
Uses TypedDict for LangGraph compatibility with Pydantic schemas.
"""
from typing import TypedDict, Literal, Optional, Any, Annotated
from pydantic import BaseModel, Field
from operator import add


# ============= Pydantic Schemas for Structured LLM Output =============

class FieldInfo(BaseModel):
    """Information about a detected form field."""
    key: str = Field(description="Unique identifier for the field")
    label: str = Field(description="Label text visible on the form")
    field_type: Literal["text", "email", "phone", "select", "date", "password", "textarea", "checkbox", "radio"] = Field(
        description="Type of input field"
    )
    is_filled: bool = Field(default=False, description="Whether the field already has a value")
    is_required: bool = Field(default=True, description="Whether the field is required")
    current_value: Optional[str] = Field(default=None, description="Current value if filled")
    options: Optional[list[str]] = Field(default=None, description="Options for select fields")
    needs_user_data: bool = Field(default=True, description="Whether we have matching user data")


class ButtonInfo(BaseModel):
    """Information about a detected button."""
    text: str = Field(description="Button text")
    button_type: Literal["submit", "continue", "login", "next", "cancel", "other"] = Field(
        description="Type of button"
    )
    is_primary: bool = Field(default=False, description="Whether this appears to be the main action button")


class PageAnalysis(BaseModel):
    """
    Structured output from LLM page analysis.
    Used with Gemini's structured output feature.
    """
    page_type: Literal["login", "otp_input", "form", "captcha", "success", "error", "loading", "unknown"] = Field(
        description="The type of page currently displayed"
    )
    page_title: Optional[str] = Field(default=None, description="Page title if visible")
    
    # Fields detection
    detected_fields: list[FieldInfo] = Field(default_factory=list, description="Form fields detected on the page")
    filled_fields: list[str] = Field(default_factory=list, description="Keys of fields that are already filled")
    remaining_fields: list[str] = Field(default_factory=list, description="Keys of fields that still need to be filled")
    
    # Special elements
    has_captcha: bool = Field(default=False, description="Whether a CAPTCHA is present")
    has_otp_field: bool = Field(default=False, description="Whether an OTP input is present")
    captcha_type: Optional[Literal["image", "recaptcha", "hcaptcha", "other"]] = Field(
        default=None, description="Type of captcha if present"
    )
    
    # Buttons
    buttons: list[ButtonInfo] = Field(default_factory=list, description="Buttons detected on the page")
    has_submit_button: bool = Field(default=False, description="Whether a submit/continue button is available")
    
    # Checkbox for agreement/terms (must be clicked before submit)
    checkbox_to_click: Optional[str] = Field(default=None, description="Checkbox label text that needs to be clicked")
    button_to_click: Optional[str] = Field(default=None, description="Button text to click after all checkboxes are checked")
    
    # Status
    error_message: Optional[str] = Field(default=None, description="Error message if visible on page")
    success_message: Optional[str] = Field(default=None, description="Success message if visible")
    is_form_complete: bool = Field(default=False, description="Whether all required fields are filled")
    
    # Recommended action
    next_action: Literal[
        "fill_form",
        "click_checkbox",
        "click_submit", 
        "request_otp",
        "request_captcha",
        "request_custom_input",
        "wait",
        "success",
        "error",
        "retry"
    ] = Field(description="Recommended next action based on page state")
    
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in this analysis")


class ActionHistoryEntry(BaseModel):
    """A single action taken during workflow execution."""
    action: str
    target: Optional[str] = None
    value: Optional[str] = None  # Masked for sensitive data
    timestamp: str
    success: bool = True
    error: Optional[str] = None


# ============= LangGraph State =============

class GraphState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    Uses TypedDict for compatibility with LangGraph's state management.
    """
    # Session info
    session_id: str
    exam_id: str
    user_id: str
    
    # Exam configuration
    exam_url: str
    exam_name: str
    field_mappings: dict[str, Any]
    
    # User data for form filling
    user_data: dict[str, Any]
    
    # Browser state
    page_url: str
    screenshot_base64: Optional[str]
    page_html: Optional[str]
    
    # LLM Analysis result (legacy)
    analysis: Optional[dict]  # PageAnalysis as dict
    
    # NEW: LLM Decision (from vision analysis)
    llm_decision: Optional[dict]  # ActionDecision as dict
    already_filled_fields: list[str]  # Track which fields are filled
    captcha_fail_count: int  # Track failed captcha attempts (fallback to human after 3)
    
    # Human intervention - NEW: waiting_for_input_type instead of interrupt()
    waiting_for_input_type: Optional[str]  # None, 'otp', 'captcha', or 'custom'
    pending_intervention: Optional[dict]
    received_otp: Optional[str]
    received_captcha: Optional[str]
    received_custom_inputs: dict[str, str]
    human_input_value: Optional[Any]  # Value from user input
    
    # Action tracking (using Annotated with add for append-only)
    action_history: Annotated[list[dict], add]
    
    # Progress
    current_step: str
    progress: int  # 0-100
    
    # Retry & error handling
    retry_count: int
    max_retries: int
    last_error: Optional[str]
    
    # Status
    status: Literal["running", "waiting_input", "paused", "completed", "failed"]
    result_message: Optional[str]


def create_initial_state(
    session_id: str,
    exam_id: str,
    user_id: str,
    exam_url: str,
    exam_name: str,
    field_mappings: dict,
    user_data: dict,
    max_retries: int = 3
) -> GraphState:
    """Create the initial state for a new workflow."""
    return GraphState(
        session_id=session_id,
        exam_id=exam_id,
        user_id=user_id,
        exam_url=exam_url,
        exam_name=exam_name,
        field_mappings=field_mappings,
        user_data=user_data,
        page_url="",
        screenshot_base64=None,
        page_html=None,
        analysis=None,
        llm_decision=None,
        already_filled_fields=[],
        captcha_fail_count=0,
        waiting_for_input_type=None,
        pending_intervention=None,
        received_otp=None,
        received_captcha=None,
        received_custom_inputs={},
        human_input_value=None,
        action_history=[],
        current_step="init",
        progress=0,
        retry_count=0,
        max_retries=max_retries,
        last_error=None,
        status="running",
        result_message=None,
    )
