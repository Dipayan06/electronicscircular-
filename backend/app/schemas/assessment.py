"""Assessment / recommendation schemas (FR-C, FR-D)."""
from pydantic import BaseModel, field_validator

SCREEN = ("good", "minor", "cracked")
BATTERY = ("good", "weak", "dead")
BODY = ("good", "scratched", "damaged")


class AssessmentIn(BaseModel):
    screen: str
    battery: str
    body: str
    powers_on: bool = True
    charging: bool = True
    water_damage: bool = False
    problems: str | None = None

    @field_validator("screen")
    @classmethod
    def _screen(cls, v):
        if v not in SCREEN:
            raise ValueError(f"must be one of {', '.join(SCREEN)}")
        return v

    @field_validator("battery")
    @classmethod
    def _battery(cls, v):
        if v not in BATTERY:
            raise ValueError(f"must be one of {', '.join(BATTERY)}")
        return v

    @field_validator("body")
    @classmethod
    def _body(cls, v):
        if v not in BODY:
            raise ValueError(f"must be one of {', '.join(BODY)}")
        return v


class RecommendationOut(BaseModel):
    action: str
    priority: int
    reason: str
    nextStep: str
