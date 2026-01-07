"""
Email Service
SMTP-based email notifications for workflow events.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

from app.config import settings


class EmailService:
    """
    Email notification service using SMTP.
    Sends notifications for workflow completion, failure, and intervention requests.
    """
    
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self._enabled = bool(self.user and self.password)
    
    @property
    def enabled(self) -> bool:
        """Check if email service is configured."""
        return self._enabled
    
    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email or list of emails
            subject: Email subject
            body_html: HTML body content
            body_text: Optional plain text body (fallback)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("[Email] Service not configured, skipping")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.user
            msg["To"] = to if isinstance(to, str) else ", ".join(to)
            
            # Add plain text part
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            
            # Add HTML part
            msg.attach(MIMEText(body_html, "html"))
            
            # Send
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True,
            )
            
            print(f"[Email] Sent to {to}: {subject}")
            return True
            
        except Exception as e:
            print(f"[Email] Failed to send: {e}")
            return False
    
    async def send_workflow_complete(
        self,
        to: str | list[str],
        exam_name: str,
        user_name: str,
        success: bool,
        message: str = ""
    ):
        """Send workflow completion notification."""
        status = "✅ Completed" if success else "❌ Failed"
        color = "#22c55e" if success else "#ef4444"
        
        subject = f"[Exam Automation] {exam_name} - {status}"
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 24px; max-width: 500px; margin: 0 auto; }}
            .status {{ color: {color}; font-size: 24px; font-weight: bold; margin-bottom: 16px; }}
            .label {{ color: #64748b; font-size: 12px; text-transform: uppercase; margin-bottom: 4px; }}
            .value {{ font-size: 16px; margin-bottom: 16px; }}
            .message {{ background: #334155; padding: 12px; border-radius: 8px; margin-top: 16px; }}
        </style></head>
        <body>
            <div class="card">
                <div class="status">{status}</div>
                <div class="label">Exam</div>
                <div class="value">{exam_name}</div>
                <div class="label">User</div>
                <div class="value">{user_name}</div>
                <div class="label">Time</div>
                <div class="value">{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</div>
                {f'<div class="message">{message}</div>' if message else ''}
            </div>
        </body>
        </html>
        """
        
        body_text = f"{exam_name} - {status}\nUser: {user_name}\n{message}"
        
        await self.send_email(to, subject, body_html, body_text)
    
    async def send_intervention_required(
        self,
        to: str | list[str],
        exam_name: str,
        intervention_type: str,  # "otp", "captcha", "custom"
        session_id: str
    ):
        """Send notification when human intervention is required."""
        type_labels = {
            "otp": "📱 OTP Required",
            "captcha": "🔒 Captcha Required",
            "custom": "❓ Input Required"
        }
        
        label = type_labels.get(intervention_type, "Input Required")
        subject = f"[Exam Automation] {exam_name} - {label}"
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 24px; max-width: 500px; margin: 0 auto; }}
            .alert {{ color: #f59e0b; font-size: 24px; font-weight: bold; margin-bottom: 16px; }}
            .btn {{ display: inline-block; background: #0ea5e9; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; margin-top: 16px; }}
        </style></head>
        <body>
            <div class="card">
                <div class="alert">{label}</div>
                <p>The workflow for <strong>{exam_name}</strong> is waiting for your input.</p>
                <a href="http://localhost:3000/workflow?sessionId={session_id}" class="btn">Open Workflow</a>
            </div>
        </body>
        </html>
        """
        
        body_text = f"{exam_name} - {label}\nOpen: http://localhost:3000/workflow?sessionId={session_id}"
        
        await self.send_email(to, subject, body_html, body_text)


# Global email service instance
email_service = EmailService()
