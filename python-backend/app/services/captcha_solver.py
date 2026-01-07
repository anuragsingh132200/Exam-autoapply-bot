"""
Captcha Solver Service
Integration with 2captcha/hCaptcha APIs for automatic captcha solving.
Falls back to human intervention if auto-solve fails.
"""
import httpx
import asyncio
from typing import Optional, Literal
from app.config import settings


class CaptchaSolverService:
    """
    Captcha auto-solve service using third-party APIs.
    Supports 2captcha and hCaptcha solver services.
    """
    
    def __init__(self):
        self.provider = settings.captcha_provider
        self.api_key = settings.captcha_api_key
        self._enabled = bool(self.provider and self.api_key)
        
        self.api_urls = {
            "2captcha": {
                "submit": "https://2captcha.com/in.php",
                "result": "https://2captcha.com/res.php"
            },
            "hcaptcha": {
                "submit": "https://api.hcaptcha-solver.com/submit",
                "result": "https://api.hcaptcha-solver.com/result"
            }
        }
    
    @property
    def enabled(self) -> bool:
        """Check if captcha solver is configured."""
        return self._enabled
    
    async def solve_image_captcha(
        self,
        image_base64: str,
        timeout_seconds: int = 60
    ) -> Optional[str]:
        """
        Solve an image-based captcha.
        
        Args:
            image_base64: Base64-encoded captcha image
            timeout_seconds: Maximum time to wait for solution
        
        Returns:
            Captcha solution text, or None if failed
        """
        if not self.enabled:
            print("[Captcha] Solver not configured")
            return None
        
        if self.provider == "2captcha":
            return await self._solve_2captcha(image_base64, timeout_seconds)
        
        print(f"[Captcha] Unknown provider: {self.provider}")
        return None
    
    async def solve_recaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout_seconds: int = 120
    ) -> Optional[str]:
        """
        Solve a reCAPTCHA v2.
        
        Args:
            site_key: The reCAPTCHA site key
            page_url: URL of the page with captcha
            timeout_seconds: Maximum time to wait
        
        Returns:
            reCAPTCHA response token, or None if failed
        """
        if not self.enabled:
            return None
        
        if self.provider == "2captcha":
            return await self._solve_2captcha_recaptcha(site_key, page_url, timeout_seconds)
        
        return None
    
    async def _solve_2captcha(
        self,
        image_base64: str,
        timeout: int
    ) -> Optional[str]:
        """Solve image captcha using 2captcha API."""
        try:
            async with httpx.AsyncClient() as client:
                # Submit captcha
                submit_resp = await client.post(
                    self.api_urls["2captcha"]["submit"],
                    data={
                        "key": self.api_key,
                        "method": "base64",
                        "body": image_base64,
                        "json": 1
                    }
                )
                
                submit_data = submit_resp.json()
                if submit_data.get("status") != 1:
                    print(f"[Captcha] Submit failed: {submit_data}")
                    return None
                
                request_id = submit_data.get("request")
                
                # Poll for result
                for _ in range(timeout // 5):
                    await asyncio.sleep(5)
                    
                    result_resp = await client.get(
                        self.api_urls["2captcha"]["result"],
                        params={
                            "key": self.api_key,
                            "action": "get",
                            "id": request_id,
                            "json": 1
                        }
                    )
                    
                    result_data = result_resp.json()
                    
                    if result_data.get("status") == 1:
                        solution = result_data.get("request")
                        print(f"[Captcha] Solved successfully")
                        return solution
                    
                    if result_data.get("request") != "CAPCHA_NOT_READY":
                        print(f"[Captcha] Error: {result_data}")
                        return None
                
                print("[Captcha] Timeout waiting for solution")
                return None
                
        except Exception as e:
            print(f"[Captcha] Error: {e}")
            return None
    
    async def _solve_2captcha_recaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """Solve reCAPTCHA using 2captcha API."""
        try:
            async with httpx.AsyncClient() as client:
                # Submit
                submit_resp = await client.post(
                    self.api_urls["2captcha"]["submit"],
                    data={
                        "key": self.api_key,
                        "method": "userrecaptcha",
                        "googlekey": site_key,
                        "pageurl": page_url,
                        "json": 1
                    }
                )
                
                submit_data = submit_resp.json()
                if submit_data.get("status") != 1:
                    return None
                
                request_id = submit_data.get("request")
                
                # Poll for result
                for _ in range(timeout // 5):
                    await asyncio.sleep(5)
                    
                    result_resp = await client.get(
                        self.api_urls["2captcha"]["result"],
                        params={
                            "key": self.api_key,
                            "action": "get",
                            "id": request_id,
                            "json": 1
                        }
                    )
                    
                    result_data = result_resp.json()
                    
                    if result_data.get("status") == 1:
                        return result_data.get("request")
                    
                    if result_data.get("request") != "CAPCHA_NOT_READY":
                        return None
                
                return None
                
        except Exception as e:
            print(f"[Captcha] reCAPTCHA error: {e}")
            return None


# Global captcha solver instance
captcha_solver = CaptchaSolverService()
