from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base


class DhyaanCheckin(Base):
    __tablename__ = "dhyaan_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mood_score = Column(Integer, nullable=False)  # 1-5
    journal_entry = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", backref="dhyaan_checkins")


class MeditationSession(Base):
    __tablename__ = "meditation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    meditation_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    current_feeling = Column(String, nullable=True)
    desired_feeling = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    title = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    audio_url = Column(String, nullable=True)
    background_music_url = Column(String, nullable=True)
    script = Column(Text, nullable=True)
    guidance_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", backref="meditation_sessions")
