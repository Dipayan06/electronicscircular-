"""Authentication business logic (FR-A). Owns registration + credential checks."""
from sqlalchemy.orm import Session

from ..models import User, Role
from ..schemas.auth import RegisterIn
from ..utils.responses import APIError
from ..utils.security import hash_password, verify_password


def register_user(db: Session, data: RegisterIn) -> User:
    # Enforce unique email (FR-A, acceptance criteria).
    if db.query(User).filter(User.email == data.email).first():
        raise APIError("An account with this email already exists", status_code=409)

    role = db.query(Role).filter(Role.name == data.role).first()
    if not role:
        raise APIError("Invalid role", status_code=400)

    user = User(
        name=data.name,
        email=str(data.email),
        password_hash=hash_password(data.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    # Same message whether the email or the password is wrong (don't leak which).
    if not user or not verify_password(password, user.password_hash):
        raise APIError("Invalid email or password", status_code=401)
    return user
