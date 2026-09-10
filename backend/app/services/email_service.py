import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional
from app.core.config import settings

logger = logging.getLogger("civicpulse.auth.email")


class EmailOTPProvider(ABC):
    """Abstract interface for dispatching OTP authentication emails."""

    @abstractmethod
    def send_otp(self, email: str, otp: str) -> bool:
        """Dispatches an OTP verification code to the recipient email."""
        pass


class ConsoleEmailProvider(EmailOTPProvider):
    """
    Development and testing provider.
    Outputs OTP codes to the secure server console and keeps an in-memory
    reference for automated test assertions.
    """

    def __init__(self):
        # In-memory store of recent OTPs for local development and test inspection
        self.sent_otps: Dict[str, str] = {}

    def send_otp(self, email: str, otp: str) -> bool:
        normalized_email = email.strip().lower()
        self.sent_otps[normalized_email] = otp
        logger.info(f"[DEV CONSOLE EMAIL] To: {normalized_email} | CivicPulse OTP: {otp} | Expires in: {settings.OTP_EXPIRE_MINUTES} min")
        return True

    def get_last_otp(self, email: str) -> Optional[str]:
        """Test helper to retrieve the latest dispatched OTP code."""
        return self.sent_otps.get(email.strip().lower())

    def clear(self):
        """Clears test OTP history."""
        self.sent_otps.clear()


class SMTPEmailProvider(EmailOTPProvider):
    """Production-capable SMTP provider using environment-configured credentials."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.EMAIL_FROM

    def send_otp(self, email: str, otp: str) -> bool:
        if not self.host or not self.sender:
            logger.error("SMTP host or sender not configured. Cannot dispatch OTP.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your CivicPulse Verification Code"
        msg["From"] = self.sender
        msg["To"] = email

        text_content = (
            f"Your CivicPulse verification code is: {otp}\n\n"
            f"This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
            "If you did not request this verification code, you can safely ignore this message."
        )
        msg.attach(MIMEText(text_content, "plain"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception as exc:
            logger.error(f"Failed to dispatch SMTP email to {email}: {exc}")
            return False


# Singleton default provider instance
_default_provider: Optional[EmailOTPProvider] = None


def get_email_provider() -> EmailOTPProvider:
    """Returns configured EmailOTPProvider singleton."""
    global _default_provider
    if _default_provider is None:
        if settings.EMAIL_PROVIDER.lower() == "smtp" and settings.SMTP_HOST:
            _default_provider = SMTPEmailProvider()
        else:
            _default_provider = ConsoleEmailProvider()
    return _default_provider


def set_email_provider(provider: EmailOTPProvider) -> None:
    """Override provider (primarily used in tests)."""
    global _default_provider
    _default_provider = provider
