from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum, CheckConstraint, func
from sqlalchemy.orm import relationship

from app.db.db import Base

class AnalysisInsight(Base):
    __tablename__ = "analysis_insights"

    id = Column(Integer, primary_key=True)
    file_id = Column(String(50), index=True, nullable=False, unique=True)
    file_analysis = Column(Text, nullable=False)
    insight_name = Column(String(255), index=True, nullable=False)
    previous_response_id = Column(String(255), index=True, nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chat_messages = relationship("ChatMessages", backref="insight", cascade="all, delete-orphan")

class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    type = Column(String(10), index=True, nullable=False)
    insight_id = Column(Integer, ForeignKey("analysis_insights.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('output', 'input')", name="check_type"),
    )
