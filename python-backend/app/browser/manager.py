"""
Browser Context Manager
Manages browser instances for workflow sessions.
"""
from typing import Optional
from app.browser.stagehand import StagehandBrowser


class BrowserManager:
    """
    Manages browser instances for active workflow sessions.
    Each session gets its own browser instance.
    """
    
    _instances: dict[str, StagehandBrowser] = {}
    
    @classmethod
    async def get_or_create(cls, session_id: str, headless: bool = False) -> StagehandBrowser:
        """Get existing browser or create new one for session."""
        if session_id not in cls._instances:
            from app.api.websocket import send_screenshot, send_log
            
            async def on_screenshot(image_base64: str, step: str):
                await send_screenshot(session_id, image_base64, step)
            
            async def on_log(message: str, level: str):
                await send_log(session_id, message, level)
            
            browser = StagehandBrowser(
                headless=headless,
                on_screenshot=on_screenshot,
                on_log=on_log,
            )
            await browser.init()
            cls._instances[session_id] = browser
        
        return cls._instances[session_id]
    
    @classmethod
    def get(cls, session_id: str) -> Optional[StagehandBrowser]:
        """Get browser instance for session if it exists."""
        return cls._instances.get(session_id)
    
    @classmethod
    async def close(cls, session_id: str):
        """Close and remove browser for session."""
        if session_id in cls._instances:
            browser = cls._instances.pop(session_id)
            await browser.close()
    
    @classmethod
    async def close_all(cls):
        """Close all browser instances."""
        for session_id in list(cls._instances.keys()):
            await cls.close(session_id)
