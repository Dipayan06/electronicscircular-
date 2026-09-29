"""Circular assistant (small language model) request schemas."""
from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class ParseIn(BaseModel):
    text: str = Field(min_length=3, max_length=600)


class DeviceRefIn(BaseModel):
    device_id: int
