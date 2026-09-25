"""Auth dependencies (Phase 1 §1.7 cross-cutting concern).

`get_current_user` resolves the JWT into a User (used to protect endpoints).
`require_role(...)` builds a dependency that also enforces role-based access
(FR-A5). HTTPBearer gives Swagger an "Authorize" button to paste a token into.
"""
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..utils.responses import APIError
from ..utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise APIError("Not authenticated", status_code=401)
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first() if user_id else None
    if not user:
        raise APIError("User no longer exists", status_code=401)
    return user


def require_role(*allowed_roles: str):
    """Dependency factory: allow only users whose role is in allowed_roles."""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise APIError("You do not have permission to perform this action", status_code=403)
        return current_user
    return checker


def require_verified(current_user: User = Depends(get_current_user)) -> User:
    """Gate sensitive actions (selling, transacting) behind email verification
    (Feature 1). Server-authoritative — verification cannot be faked client-side."""
    if not current_user.is_verified:
        raise APIError("Please verify your email address to do this.", status_code=403)
    return current_user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user, but anonymous callers get None instead of 401.
    Used by public reads that reveal a bit more to the owner/admin."""
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except APIError:
        return None
