from sqlalchemy.orm import Session
from app.models.meeting import Meeting
from app.repositories.base import BaseRepository

class MeetingRepository(BaseRepository[Meeting]):
    def __init__(self):
        super().__init__(Meeting)
        
    def get_all_ordered(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(self.model).order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()

meeting_repo = MeetingRepository()
