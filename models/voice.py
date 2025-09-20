from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    context = Column(String, nullable=True)
    status = Column(String, default="active", index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    stopped_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="voice_sessions")
    messages = relationship(
        "VoiceMessage", back_populates="session", cascade="all, delete-orphan"
    )


class VoiceMessage(Base):
    __tablename__ = "voice_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer, ForeignKey("voice_sessions.id"), nullable=False, index=True
    )
    role = Column(String, nullable=False)  # 'user' or 'ai'
    text = Column(Text, nullable=False)
    confidence = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    session = relationship("VoiceSession", back_populates="messages")
