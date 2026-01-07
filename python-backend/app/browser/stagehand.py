"""
Stagehand Browser Wrapper
Python wrapper for browser automation using Playwright with AI-powered actions.

Note: This Python implementation uses Playwright directly since Stagehand is TypeScript-only.
We use our LLM service for AI-powered action interpretation similar to Stagehand's page.act().
"""
import asyncio
import base64
from typing import Optional, Callable, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from datetime import datetime

from app.config import settings
from app.services.llm import llm_service


class StagehandBrowser:
    """
    AI-powered browser automation wrapper.
    Provides Stagehand-like functionality using Playwright + Gemini.
    
    Key methods mirror Stagehand's API:
    - goto(url): Navigate to URL
    - act(instruction): AI-powered action execution
    - observe(): Get page state
    - screenshot(): Capture page screenshot
    """
    
    def __init__(
        self,
        headless: bool = False,
        viewport_width: int = 1024,
        viewport_height: int = 768,
        on_screenshot: Optional[Callable[[str, str], Any]] = None,
        on_log: Optional[Callable[[str, str], Any]] = None,
    ):
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.on_screenshot = on_screenshot
        self.on_log = on_log
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
    async def init(self):
        """Initialize browser and page."""
        await self._log("Initializing browser...")
        
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        self._context = await self._browser.new_context(
            viewport={"width": self.viewport_width, "height": self.viewport_height},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self._page = await self._context.new_page()
        
        # Set default timeout
        self._page.set_default_timeout(30000)
        
        await self._log("Browser initialized")
        
    async def close(self):
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        await self._log("Browser closed")
    
    @property
    def page(self) -> Page:
        """Get the Playwright page object."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call init() first.")
        return self._page
    
    async def goto(self, url: str) -> str:
        """Navigate to URL."""
        await self._log(f"Navigating to: {url}")
        await self.page.goto(url, wait_until="domcontentloaded")
        await self._wait_for_stable()
        return self.page.url
    
    async def screenshot(self, step: str = "capture") -> str:
        """
        Capture page screenshot as base64.
        Broadcasts to callback if provided.
        """
        screenshot_bytes = await self.page.screenshot(type="png", full_page=False)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        
        if self.on_screenshot:
            await self.on_screenshot(screenshot_base64, step)
        
        return screenshot_base64
    
    async def act(self, instruction: str) -> bool:
        """
        AI-powered action execution.
        Similar to Stagehand's page.act() - interprets natural language instructions.
        
        Examples:
        - "click on login button"
        - "type 'hello' into email field"
        - "select '12th' from class dropdown"
        """
        await self._log(f"Acting: {instruction}")
        
        try:
            # Determine action type from instruction
            instruction_lower = instruction.lower()
            
            if "click" in instruction_lower:
                await self._handle_click(instruction)
            elif "type" in instruction_lower or "enter" in instruction_lower:
                await self._handle_type(instruction)
            elif "select" in instruction_lower:
                await self._handle_select(instruction)
            elif "wait" in instruction_lower:
                await asyncio.sleep(2)
            else:
                # Try generic click/interaction
                await self._handle_generic_action(instruction)
            
            # Wait for page to stabilize after action
            await self._wait_for_stable()
            return True
            
        except Exception as e:
            await self._log(f"Action failed: {str(e)}", level="error")
            return False
    
    async def observe(self) -> dict:
        """
        Observe current page state.
        Returns information about visible elements.
        """
        url = self.page.url
        title = await self.page.title()
        
        # Get visible form fields
        fields = await self._get_form_fields()
        
        # Get visible buttons
        buttons = await self._get_buttons()
        
        return {
            "url": url,
            "title": title,
            "fields": fields,
            "buttons": buttons,
        }
    
    async def fill_field(self, selector_or_label: str, value: str) -> bool:
        """
        Fill a form field by selector or label.
        Uses multiple strategies to find and fill the field.
        """
        await self._log(f"Filling field: {selector_or_label}")
        
        try:
            # Try direct selector first
            try:
                element = await self.page.query_selector(selector_or_label)
                if element:
                    await element.fill(value)
                    return True
            except Exception:
                pass
            
            # Try by placeholder
            try:
                element = await self.page.query_selector(f'input[placeholder*="{selector_or_label}" i]')
                if element:
                    await element.fill(value)
                    return True
            except Exception:
                pass
            
            # Try by label text
            try:
                # Find label and get associated input
                label = await self.page.query_selector(f'label:has-text("{selector_or_label}")')
                if label:
                    for_attr = await label.get_attribute("for")
                    if for_attr:
                        element = await self.page.query_selector(f'#{for_attr}')
                        if element:
                            await element.fill(value)
                            return True
            except Exception:
                pass
            
            # Try by name attribute
            try:
                element = await self.page.query_selector(f'input[name*="{selector_or_label}" i]')
                if element:
                    await element.fill(value)
                    return True
            except Exception:
                pass
            
            await self._log(f"Could not find field: {selector_or_label}", level="warning")
            return False
            
        except Exception as e:
            await self._log(f"Fill failed: {str(e)}", level="error")
            return False
    
    async def click_button(self, text_or_selector: str) -> bool:
        """
        Click a button by text or selector.
        """
        await self._log(f"Clicking: {text_or_selector}")
        
        try:
            # Try exact text match
            try:
                await self.page.click(f'button:has-text("{text_or_selector}")', timeout=5000)
                return True
            except Exception:
                pass
            
            # Try input submit
            try:
                await self.page.click(f'input[value*="{text_or_selector}" i]', timeout=5000)
                return True
            except Exception:
                pass
            
            # Try any clickable element with text
            try:
                await self.page.click(f'text="{text_or_selector}"', timeout=5000)
                return True
            except Exception:
                pass
            
            # Try selector directly
            try:
                await self.page.click(text_or_selector, timeout=5000)
                return True
            except Exception:
                pass
            
            await self._log(f"Could not find button: {text_or_selector}", level="warning")
            return False
            
        except Exception as e:
            await self._log(f"Click failed: {str(e)}", level="error")
            return False
    
    async def select_option(self, selector_or_label: str, value: str) -> bool:
        """
        Select an option from a dropdown.
        """
        await self._log(f"Selecting: {value} from {selector_or_label}")
        
        try:
            # Try by label value
            try:
                await self.page.select_option(
                    f'select:near(:text("{selector_or_label}"))',
                    label=value,
                    timeout=5000
                )
                return True
            except Exception:
                pass
            
            # Try clicking to open dropdown, then selecting
            try:
                # Click the dropdown trigger
                await self.page.click(f'text="{selector_or_label}"', timeout=3000)
                await asyncio.sleep(0.5)
                # Click the option
                await self.page.click(f'text="{value}"', timeout=3000)
                return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            await self._log(f"Select failed: {str(e)}", level="error")
            return False
    
    async def get_page_html(self) -> str:
        """Get page HTML content."""
        return await self.page.content()
    
    async def wait_for_navigation(self, timeout: int = 30000):
        """Wait for navigation to complete."""
        await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
    
    # ============= Private Helper Methods =============
    
    async def _wait_for_stable(self, timeout_ms: int = 2000):
        """Wait for DOM to stabilize after actions."""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            # Timeout is ok, just continue
            pass
        await asyncio.sleep(0.5)
    
    async def _handle_click(self, instruction: str):
        """Handle click instructions."""
        # Extract target from instruction
        # e.g., "click on login button" -> "login button"
        import re
        match = re.search(r"click (?:on |the )?(.+)", instruction, re.IGNORECASE)
        if match:
            target = match.group(1).strip()
            await self.click_button(target)
    
    async def _handle_type(self, instruction: str):
        """Handle type/enter instructions."""
        # e.g., "type 'hello' into email field"
        import re
        match = re.search(r"type ['\"](.+?)['\"] (?:into |in )?(.+)", instruction, re.IGNORECASE)
        if match:
            value = match.group(1)
            field = match.group(2).strip()
            await self.fill_field(field, value)
        else:
            # Try simpler pattern: "enter '123456' in otp"
            match = re.search(r"enter ['\"](.+?)['\"] (?:into |in )?(.+)", instruction, re.IGNORECASE)
            if match:
                value = match.group(1)
                field = match.group(2).strip()
                await self.fill_field(field, value)
    
    async def _handle_select(self, instruction: str):
        """Handle select instructions."""
        # e.g., "select '12th' from class dropdown"
        import re
        match = re.search(r"select ['\"]?(.+?)['\"]? (?:from |in |as )?(.+)", instruction, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            dropdown = match.group(2).strip()
            await self.select_option(dropdown, value)
    
    async def _handle_generic_action(self, instruction: str):
        """Handle generic actions using AI."""
        # For complex instructions, use LLM to determine action
        # This is a fallback for instructions we can't parse
        await self._log(f"Attempting generic action: {instruction}")
        
        # Try to find and click any element matching the instruction
        try:
            await self.page.click(f'text=/{instruction}/i', timeout=5000)
        except Exception:
            await self._log(f"Could not execute: {instruction}", level="warning")
    
    async def _get_form_fields(self) -> list[dict]:
        """Get all visible form fields."""
        fields = []
        
        try:
            inputs = await self.page.query_selector_all('input:visible, textarea:visible, select:visible')
            
            for input_elem in inputs[:20]:  # Limit to 20 fields
                try:
                    input_type = await input_elem.get_attribute("type") or "text"
                    name = await input_elem.get_attribute("name") or ""
                    placeholder = await input_elem.get_attribute("placeholder") or ""
                    value = await input_elem.get_attribute("value") or ""
                    
                    fields.append({
                        "type": input_type,
                        "name": name,
                        "placeholder": placeholder,
                        "has_value": bool(value),
                    })
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return fields
    
    async def _get_buttons(self) -> list[dict]:
        """Get all visible buttons."""
        buttons = []
        
        try:
            btn_elements = await self.page.query_selector_all('button:visible, input[type="submit"]:visible')
            
            for btn in btn_elements[:10]:  # Limit to 10 buttons
                try:
                    text = await btn.text_content() or ""
                    value = await btn.get_attribute("value") or ""
                    
                    buttons.append({
                        "text": text.strip() or value,
                    })
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return buttons
    
    async def _log(self, message: str, level: str = "info"):
        """Log a message."""
        print(f"[Browser] {message}")
        if self.on_log:
            await self.on_log(message, level)


# Convenience function to create browser instance
async def create_browser(
    session_id: str = None,
    headless: bool = False,
) -> StagehandBrowser:
    """
    Create and initialize a browser instance.
    
    Args:
        session_id: Optional session ID for WebSocket callbacks
        headless: Whether to run in headless mode
    
    Returns:
        Initialized StagehandBrowser instance
    """
    from app.api.websocket import send_screenshot, send_log
    
    async def on_screenshot(image_base64: str, step: str):
        if session_id:
            await send_screenshot(session_id, image_base64, step)
    
    async def on_log(message: str, level: str):
        if session_id:
            await send_log(session_id, message, level)
    
    browser = StagehandBrowser(
        headless=headless,
        on_screenshot=on_screenshot,
        on_log=on_log,
    )
    
    await browser.init()
    return browser
