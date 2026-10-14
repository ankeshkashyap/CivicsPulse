from unittest.mock import MagicMock, patch
import pytest
from app.core.config import Settings
from app.services.email_service import (
    ConsoleEmailProvider,
    SMTPEmailProvider,
    get_email_provider,
    set_email_provider,
    reset_email_provider,
)


def test_console_email_provider():
    """Verifies ConsoleEmailProvider records OTPs in-memory for testing."""
    provider = ConsoleEmailProvider()
    assert provider.send_otp("citizen@example.com", "123456") is True
    assert provider.get_last_otp("citizen@example.com") == "123456"
    assert provider.get_last_otp("CITIZEN@EXAMPLE.COM") == "123456"  # case-insensitive lookup
    provider.clear()
    assert provider.get_last_otp("citizen@example.com") is None


def test_settings_smtp_aliases():
    """Verifies Settings synchronizes SMTP_USERNAME/SMTP_USER and SMTP_FROM_EMAIL/EMAIL_FROM."""
    s = Settings(
        SMTP_USERNAME="ankeshkashyap2222@gmail.com",
        SMTP_FROM_EMAIL="ankeshkashyap2222@gmail.com",
        SMTP_USE_TLS=True,
    )
    assert s.SMTP_USER == "ankeshkashyap2222@gmail.com"
    assert s.EMAIL_FROM == "ankeshkashyap2222@gmail.com"
    assert s.effective_smtp_username == "ankeshkashyap2222@gmail.com"
    assert s.effective_smtp_from_email == "ankeshkashyap2222@gmail.com"
    assert s.SMTP_USE_TLS is True


def test_smtp_provider_initialization():
    """Verifies SMTPEmailProvider initializes from parameters or settings."""
    provider = SMTPEmailProvider(
        host="smtp.gmail.com",
        port=587,
        username="ankeshkashyap2222@gmail.com",
        password="secret-test-password",
        from_email="ankeshkashyap2222@gmail.com",
        use_tls=True,
    )
    assert provider.host == "smtp.gmail.com"
    assert provider.port == 587
    assert provider.user == "ankeshkashyap2222@gmail.com"
    assert provider.password == "secret-test-password"
    assert provider.sender == "ankeshkashyap2222@gmail.com"
    assert provider.use_tls is True


def test_smtp_provider_unconfigured_fails_gracefully():
    """Verifies SMTPEmailProvider returns False without exception when unconfigured."""
    provider = SMTPEmailProvider(host="", from_email="")
    assert provider.send_otp("user@example.com", "123456") is False


@patch("smtplib.SMTP")
def test_smtp_provider_send_otp_success(mock_smtp_cls):
    """Verifies SMTPEmailProvider sends valid MIME message with STARTTLS and credentials."""
    mock_server = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_server

    provider = SMTPEmailProvider(
        host="smtp.gmail.com",
        port=587,
        username="ankeshkashyap2222@gmail.com",
        password="mock-app-password",
        from_email="ankeshkashyap2222@gmail.com",
        use_tls=True,
    )

    success = provider.send_otp("citizen@example.com", "654321")
    assert success is True

    # Check connection parameters
    mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("ankeshkashyap2222@gmail.com", "mock-app-password")

    # Check sent message
    mock_server.send_message.assert_called_once()
    sent_msg = mock_server.send_message.call_args[0][0]
    assert sent_msg["From"] == "ankeshkashyap2222@gmail.com"
    assert sent_msg["To"] == "citizen@example.com"
    assert sent_msg["Subject"] == "Your CivicPulse Verification Code"
    # Ensure OTP is inside payload
    payload = sent_msg.get_payload()[0].get_payload()
    assert "654321" in payload


@patch("smtplib.SMTP")
def test_smtp_provider_send_otp_connection_failure_handled(mock_smtp_cls):
    """Verifies that an SMTP exception is safely caught and returns False without raising."""
    import smtplib
    mock_smtp_cls.side_effect = smtplib.SMTPConnectError(421, b"Connection refused")

    provider = SMTPEmailProvider(
        host="smtp.gmail.com",
        port=587,
        username="ankeshkashyap2222@gmail.com",
        password="mock-password",
        from_email="ankeshkashyap2222@gmail.com",
        use_tls=True,
    )

    # Should not raise exception
    success = provider.send_otp("citizen@example.com", "112233")
    assert success is False
