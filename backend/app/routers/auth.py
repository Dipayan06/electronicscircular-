"""Authentication endpoints (FR-A1..A5 + Feature 1 email verification)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.auth import RegisterIn, LoginIn, VerifyIn, UserOut, AuthOut
from ..services import auth_service
from ..utils.responses import success, APIError
from ..utils.security import create_access_token
from ..utils import email as email_util

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", summary="Register a new account (sends a verification code)")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, data)
    token = create_access_token(user.id, user.role.name)
    out = AuthOut(token=token, user=UserOut.from_user(user))
    return success(out, "Account created — check your email for a verification code")


@router.post("/login", summary="Log in and receive a JWT")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, str(data.email), data.password)
    token = create_access_token(user.id, user.role.name)
    out = AuthOut(token=token, user=UserOut.from_user(user))
    return success(out, "Logged in")


@router.get("/me", summary="Get the current authenticated user")
def me(current_user: User = Depends(get_current_user)):
    return success(UserOut.from_user(current_user), "Current user")


@router.post("/verify-email", summary="Verify email with the one-time code")
def verify_email(data: VerifyIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    updated = auth_service.verify_email(db, user, data.code)
    return success(UserOut.from_user(updated), "Email verified")


@router.post("/resend-verification", summary="Resend the verification code (rate-limited)")
def resend_verification(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    auth_service.resend_verification(db, user)
    return success(None, "Verification code sent")


@router.get("/dev/verification-code", summary="[DEV ONLY] Fetch your own pending code")
def dev_code(user: User = Depends(get_current_user)):
    """Dev-mode helper so verification can be completed without a mail server.
    Returns ONLY the caller's own code, and only while EMAIL_DEV_MODE is on."""
    if not settings.EMAIL_DEV_MODE:
        raise APIError("Not available", status_code=404)
    code = email_util.get_dev_code(user.id)
    if not code:
        raise APIError("No pending code — request one via resend.", status_code=404)
    return success({"code": code}, "Dev verification code")
