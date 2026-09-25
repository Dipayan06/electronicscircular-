"""Email verification model (Feature 1).

Stores a *hashed* one-time code (never the plaintext OTP), an expiry, a
single-use flag, and an attempt counter. The plaintext code only ever exists
transiently in memory when generated/sent — it is never persisted or logged.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)   # bcrypt hash of the OTP
    expires_at = Column(DateTime, nullable=False)
    consumed = Column(Boolean, default=False, nullable=False)   # single-use guard
    attempts = Column(Integer, default=0, nullable=False)        # wrong-code attempts
    sends_this_hour = Column(Integer, default=1, nullable=False) # resend rate limiting
    last_sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
