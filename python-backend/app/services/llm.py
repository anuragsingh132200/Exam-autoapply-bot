"""
LLM Service
Gemini 3 Flash with structured output support using LangChain.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import Type, TypeVar
import base64

from app.config import settings
from app.graph.state import PageAnalysis


T = TypeVar("T", bound=BaseModel)


class LLMService:
    """
    LLM service using Gemini 3 Flash via LangChain.
    Provides structured output capabilities.
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # Using gemini-2.0-flash as gemini-3-flash may not be available yet
            google_api_key=settings.google_api_key,
            temperature=0.1,  # Low temperature for consistent structured output
        )
    
    def with_structured_output(self, schema: Type[T]) -> ChatGoogleGenerativeAI:
        """
        Get LLM instance configured for structured output.
        Uses LangChain's built-in with_structured_output method.
        """
        return self.llm.with_structured_output(schema)
    
    async def analyze_page(
        self,
        screenshot_base64: str,
        page_html: str = None,
        user_data: dict = None,
        field_mappings: dict = None,
        action_history: list = None,
    ) -> PageAnalysis:
        """
        Analyze a web page using vision capabilities.
        Returns structured PageAnalysis.
        """
        # Build the prompt
        system_prompt = """You are an expert web page analyzer for form automation.
Analyze the provided screenshot and determine:
1. What type of page this is (login, form, OTP input, captcha, success, error)
2. What form fields are visible and their current state
3. What buttons are available
4. Whether there are any captchas or OTP fields
5. What the next action should be

Be precise and thorough. Focus on actionable information for form automation."""

        # Build context message
        context_parts = []
        
        if user_data:
            # Only show field keys, not values for privacy
            available_fields = list(user_data.keys())
            context_parts.append(f"Available user data fields: {available_fields}")
        
        if field_mappings:
            context_parts.append(f"Expected field mappings: {list(field_mappings.keys())}")
        
        if action_history:
            # Show last 3 actions
            recent_actions = action_history[-3:] if len(action_history) > 3 else action_history
            context_parts.append(f"Recent actions: {recent_actions}")
        
        context = "\n".join(context_parts) if context_parts else "No additional context."
        
        # Create message with image
        human_message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"Analyze this web page for form automation.\n\nContext:\n{context}\n\nProvide a structured analysis."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"}
                }
            ]
        )
        
        # Get structured output
        structured_llm = self.with_structured_output(PageAnalysis)
        
        try:
            result = await structured_llm.ainvoke([
                SystemMessage(content=system_prompt),
                human_message
            ])
            return result
        except Exception as e:
            # Return a default analysis on error
            return PageAnalysis(
                page_type="unknown",
                next_action="retry",
                confidence=0.0,
                error_message=str(e)
            )
    
    async def extract_captcha_text(self, captcha_image_base64: str) -> str:
        """
        Attempt to extract text from a simple captcha image.
        Note: This won't work for complex captchas like reCAPTCHA.
        """
        human_message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "This is a CAPTCHA image. Extract and return ONLY the text/characters shown in the image. Return just the characters, nothing else."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{captcha_image_base64}"}
                }
            ]
        )
        
        try:
            result = await self.llm.ainvoke([human_message])
            return result.content.strip()
        except Exception:
            return ""
    
    async def suggest_field_mapping(
        self,
        field_label: str,
        user_data_keys: list[str]
    ) -> str:
        """
        Suggest which user data field maps to a form field label.
        Uses semantic similarity.
        """
        prompt = f"""Given a form field with label "{field_label}", which of these user data fields is the best match?

Available fields: {user_data_keys}

Return ONLY the field name that best matches, or "unknown" if no good match exists."""

        try:
            result = await self.llm.ainvoke([HumanMessage(content=prompt)])
            suggestion = result.content.strip()
            
            # Validate suggestion is in available fields
            if suggestion in user_data_keys:
                return suggestion
            return "unknown"
        except Exception:
            return "unknown"


# Global LLM service instance
llm_service = LLMService()
