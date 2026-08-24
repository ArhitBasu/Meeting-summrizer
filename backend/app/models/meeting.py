from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.base import Base

class MeetingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    TRANSCRIBING = "TRANSCRIBING"
    TRANSCRIBED = "TRANSCRIBED"
    SUMMARIZING = "SUMMARIZING"
    COMPLETED = "COMPLETED"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    SUMMARIZATION_FAILED = "SUMMARIZATION_FAILED"

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    title = Column(String, nullable=True)
    status = Column(Enum(MeetingStatus), default=MeetingStatus.UPLOADED)
    duration = Column(Integer, nullable=True) # in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    transcript = relationship("Transcript", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    participants = relationship("Participant", back_populates="meeting", cascade="all, delete-orphan")

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), unique=True)
    text = Column(Text, nullable=False)
    
    meeting = relationship("Meeting", back_populates="transcript")

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), unique=True)
    overview = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=False)
    
    meeting = relationship("Meeting", back_populates="summary")

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    text = Column(Text, nullable=False)
    
    meeting = relationship("Meeting", back_populates="decisions")

class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    task = Column(Text, nullable=False)
    assignee = Column(String, nullable=True)
    deadline = Column(String, nullable=True)
    
    meeting = relationship("Meeting", back_populates="action_items")

class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    name = Column(String, nullable=False)
    
    meeting = relationship("Meeting", back_populates="participants")
