from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.meeting import MeetingStatus
from app.schemas.meeting import MeetingResponse, MeetingDetailResponse, TranscriptSchema, SummarySchema
from app.repositories.meeting import meeting_repo
from app.services.audio import AudioStorageService
from app.services.processing import MeetingProcessingService
from app.core.logging import logger

router = APIRouter()

@router.post("/upload", response_model=MeetingResponse, status_code=202)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    logger.info(f"Received file upload request: {file.filename}")
    
    try:
        AudioStorageService.validate_file(file)
    except ValueError as e:
        logger.warning(f"File validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    file_path = AudioStorageService.save_file(file)
        
    meeting = meeting_repo.create(db, obj_in={
        "filename": file.filename, 
        "title": "Processing...", 
        "status": MeetingStatus.UPLOADED
    })
    
    logger.info(f"Created meeting record ID {meeting.id} for file {file.filename}")
    
    background_tasks.add_task(
        MeetingProcessingService.process_meeting_pipeline,
        meeting.id,
        file_path
    )
    
    return meeting

@router.get("/", response_model=List[MeetingResponse])
def list_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return meeting_repo.get_all_ordered(db, skip=skip, limit=limit)

@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = meeting_repo.get(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = meeting_repo.get(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    meeting_repo.delete(db, id=meeting_id)
    logger.info(f"Deleted meeting ID {meeting_id}")
    return None

@router.get("/{meeting_id}/transcript", response_model=TranscriptSchema)
def get_meeting_transcript(meeting_id: int, db: Session = Depends(get_db)):
    meeting = meeting_repo.get(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not meeting.transcript:
        raise HTTPException(status_code=404, detail="Transcript not available")
    return meeting.transcript
    
@router.get("/{meeting_id}/summary", response_model=SummarySchema)
def get_meeting_summary(meeting_id: int, db: Session = Depends(get_db)):
    meeting = meeting_repo.get(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not meeting.summary:
        raise HTTPException(status_code=404, detail="Summary not available")
    return meeting.summary
