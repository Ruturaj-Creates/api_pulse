"""
Email delivery — mock by default, real SMTP optional.

In development we log to the console instead of sending mail.
Use MailHog (port 1025) or similar when ALERT_EMAIL_MOCK=false.
"""

import logging

import aiosmtplib
from email.message import EmailMessage

from app.core.config import Settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    settings: Settings,
) -> bool:
    """Send an email. Returns True on success."""
    if settings.alert_email_mock:
        logger.info(
            "[MOCK EMAIL] to=%s subject=%s\n%s",
            to_email,
            subject,
            body,
        )
        print(f"\n--- MOCK EMAIL ---\nTo: {to_email}\nSubject: {subject}\n\n{body}\n---\n")
        return True

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=False,
        )
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False
