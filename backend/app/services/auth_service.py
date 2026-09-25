"""Authentication business logic (FR-A + Feature 1 email verification)."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..config import settings
from ..models import User, Role, EmailVerification
from ..schemas.auth import RegisterIn
from ..utils.responses import APIError
from ..utils.security import hash_password, verify_password, generate_otp, hash_otp, verify_otp
from ..utils import email as email_util
from . import notification_service

# Feature 1: only these email domains may register (authoritative, backend-side).
ALLOWED_EMAIL_DOMAINS = ("gmail.com", "yahoo.com")


def _domain_of(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else ""


def assert_allowed_domain(email: str) -> None:
    if _domain_of(email) not in ALLOWED_EMAIL_DOMAINS:
        raise APIError("This email domain is not supported. Use a @gmail.com or @yahoo.com address.",
                       status_code=422)


def _issue_code(db: Session, user: User) -> None:
    """Generate a fresh OTP, invalidating any previous one for this user."""
    db.query(EmailVerification).filter(
        EmailVerification.user_id == user.id, EmailVerification.consumed == False  # noqa: E712
    ).update({"consumed": True})
    code = generate_otp()
    rec = EmailVerification(
        user_id=user.id,
        code_hash=hash_otp(code),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES),
    )
    db.add(rec)
    db.commit()
    # Send AFTER commit so a delivery error never leaves a phantom code.
    email_util.send_verification_email(user.id, user.email, code)


def register_user(db: Session, data: RegisterIn) -> User:
    assert_allowed_domain(str(data.email))  # defence-in-depth (schema also checks)
    if db.query(User).filter(User.email == str(data.email)).first():
        raise APIError("An account with this email already exists", status_code=409)

    role = db.query(Role).filter(Role.name == data.role).first()
    if not role:
        raise APIError("Invalid role", status_code=400)

    user = User(
        name=data.name, email=str(data.email),
        password_hash=hash_password(data.password), role_id=role.id,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _issue_code(db, user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise APIError("Invalid email or password", status_code=401)
    return user


def verify_email(db: Session, user: User, code: str) -> User:
    if user.is_verified:
        return user  # idempotent — already verified
    rec = (
        db.query(EmailVerification)
        .filter(EmailVerification.user_id == user.id, EmailVerification.consumed == False)  # noqa: E712
        .order_by(EmailVerification.created_at.desc())
        .first()
    )
    if not rec:
        raise APIError("No pending verification. Please request a new code.", status_code=400)
    if rec.expires_at < datetime.utcnow():
        rec.consumed = True
        db.commit()
        raise APIError("This code has expired. Please request a new one.", status_code=400)
    if rec.attempts >= settings.OTP_MAX_ATTEMPTS:
        rec.consumed = True
        db.commit()
        raise APIError("Too many incorrect attempts. Please request a new code.", status_code=429)

    if not verify_otp(code, rec.code_hash):
        rec.attempts += 1
        db.commit()
        raise APIError("Incorrect verification code.", status_code=400)

    # Success: single-use consume + activate.
    rec.consumed = True
    user.is_verified = True
    db.commit()
    db.refresh(user)
    notification_service.notify(
        db, user.id, "verification", "Email verified",
        "Your email address has been verified. Your account is now fully active.",
    )
    return user


def resend_verification(db: Session, user: User) -> None:
    if user.is_verified:
        raise APIError("Your account is already verified.", status_code=400)

    latest = (
        db.query(EmailVerification)
        .filter(EmailVerification.user_id == user.id)
        .order_by(EmailVerification.created_at.desc())
        .first()
    )
    now = datetime.utcnow()
    if latest:
        # Cooldown between sends.
        if (now - latest.last_sent_at).total_seconds() < settings.RESEND_COOLDOWN_SECONDS:
            wait = settings.RESEND_COOLDOWN_SECONDS - int((now - latest.last_sent_at).total_seconds())
            raise APIError(f"Please wait {wait}s before requesting another code.", status_code=429)
        # Hourly cap.
        window = (now - latest.created_at).total_seconds()
        if window < 3600 and latest.sends_this_hour >= settings.RESEND_MAX_PER_HOUR:
            raise APIError("Too many verification emails. Please try again later.", status_code=429)

    sends = (latest.sends_this_hour + 1) if (latest and (now - latest.created_at).total_seconds() < 3600) else 1
    _issue_code(db, user)
    # Track send count on the freshly created record.
    fresh = (
        db.query(EmailVerification)
        .filter(EmailVerification.user_id == user.id, EmailVerification.consumed == False)  # noqa: E712
        .order_by(EmailVerification.created_at.desc())
        .first()
    )
    if fresh:
        fresh.sends_this_hour = sends
        fresh.last_sent_at = now
        db.commit()
