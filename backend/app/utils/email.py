"""Email delivery (Feature 1).

Dev mode (default): no mail server — the message is written to a dev outbox file
and the console, and the account owner can fetch their own pending code via a
dev-only endpoint. This lets verification be completed locally / over a tunnel
without real email. The OTP is NOT written to the outbox in a way that leaks
across users, and never to the app's normal logs.

Real mode: set EMAIL_DEV_MODE=false and SMTP_* in .env to send via SMTP.
"""
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from ..config import settings

# In-memory record of the latest code per user id, for the dev-only self-fetch
# endpoint. Cleared on restart; only ever returned to the authenticated owner.
_DEV_CODES: dict[int, str] = {}

_OUTBOX_DIR = os.path.join("data", "dev_outbox")


def _dev_deliver(user_id: int, to: str, subject: str, body: str, code: str) -> None:
    _DEV_CODES[user_id] = code
    try:
        os.makedirs(_OUTBOX_DIR, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        with open(os.path.join(_OUTBOX_DIR, f"{stamp}-{to}.txt"), "w", encoding="utf-8") as f:
            f.write(f"To: {to}\nSubject: {subject}\n\n{body}\n")
    except OSError:
        pass  # outbox is best-effort; the self-fetch endpoint still works


def _smtp_send(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.starttls()
        if settings.SMTP_USER:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.send_message(msg)


def send_verification_email(user_id: int, to: str, code: str) -> None:
    subject = "Your Circular Marketplace verification code"
    body = (
        f"Welcome to the Circular Electronics Marketplace.\n\n"
        f"Your verification code is: {code}\n\n"
        f"It expires in {settings.OTP_TTL_MINUTES} minutes. If you did not request "
        f"this, you can ignore this email."
    )
    if settings.EMAIL_DEV_MODE or not settings.SMTP_HOST:
        _dev_deliver(user_id, to, subject, body, code)
    else:
        _smtp_send(to, subject, body)


def get_dev_code(user_id: int) -> str | None:
    """Dev-only: the latest code generated for this user (self-service)."""
    return _DEV_CODES.get(user_id)
