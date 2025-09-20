from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base


class MangaRequest(Base):
    __tablename__ = "manga_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    story_id = Column(String, unique=True, index=True, nullable=False)
    inputs_json = Column(Text, nullable=False)
    result_url = Column(String, nullable=True)  # First panel image URL / thumbnail
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", backref="manga_requests")
