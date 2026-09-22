"""Auth request/response schemas (FR-A). Pydantic validates at the API boundary."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

# Roles a user may self-register as (admin is created via seed only).
SELF_SIGNUP_ROLES = ("consumer", "provider", "refurbisher", "recycler", "supplier")


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = "consumer"

    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        if v not in SELF_SIGNUP_ROLES:
            raise ValueError(f"must be one of {', '.join(SELF_SIGNUP_ROLES)}")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_user(cls, user) -> "UserOut":
        return cls(id=user.id, name=user.name, email=user.email,
                   role=user.role.name, created_at=user.created_at)


class AuthOut(BaseModel):
    token: str
    user: UserOut
