"""Authentication endpoints (FR-A1..A5)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.auth import RegisterIn, LoginIn, UserOut, AuthOut
from ..services import auth_service
from ..utils.responses import success
from ..utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", summary="Register a new account")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, data)
    token = create_access_token(user.id, user.role.name)
    out = AuthOut(token=token, user=UserOut.from_user(user))
    return success(out, "Account created")


@router.post("/login", summary="Log in and receive a JWT")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, str(data.email), data.password)
    token = create_access_token(user.id, user.role.name)
    out = AuthOut(token=token, user=UserOut.from_user(user))
    return success(out, "Logged in")


@router.get("/me", summary="Get the current authenticated user")
def me(current_user: User = Depends(get_current_user)):
    return success(UserOut.from_user(current_user), "Current user")
