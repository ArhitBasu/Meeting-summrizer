from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.meeting import MeetingStatus

class ActionItemSchema(BaseModel):
    id: int
    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None

    class Config:
        from_attributes = True

class DecisionSchema(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True

class ParticipantSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class SummarySchema(BaseModel):
    overview: str
    key_points: List[str]

    class Config:
        from_attributes = True

class TranscriptSchema(BaseModel):
    text: str

    class Config:
        from_attributes = True

class MeetingBase(BaseModel):
    title: Optional[str] = None

class MeetingResponse(MeetingBase):
    id: int
    filename: str
    status: MeetingStatus
    duration: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class MeetingDetailResponse(MeetingResponse):
    transcript: Optional[TranscriptSchema] = None
    summary: Optional[SummarySchema] = None
    decisions: List[DecisionSchema] = []
    action_items: List[ActionItemSchema] = []
    participants: List[ParticipantSchema] = []
