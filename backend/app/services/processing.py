from sqlalchemy.orm import Session
from app.services.transcription import TranscriptionService
from app.services.summarization import SummarizationService
from app.database.session import SessionLocal
from app.core.logging import logger
import traceback

class MeetingProcessingService:
    @staticmethod
    def process_meeting_pipeline(meeting_id: int, file_path: str) -> None:
        """
        The background job orchestrator. 
        Instantiates a new DB session since it runs in a separate thread/task.
        """
        db: Session = SessionLocal()
        try:
            logger.info(f"Starting processing pipeline for meeting {meeting_id}")
            
            # Step 1: Transcription
            transcription_service = TranscriptionService(db)
            transcription_success = transcription_service.transcribe_meeting(meeting_id, file_path)
            
            if not transcription_success:
                logger.error(f"Pipeline halted for meeting {meeting_id} due to transcription failure.")
                return
                
            # Step 2: Summarization
            summarization_service = SummarizationService(db)
            summarization_success = summarization_service.summarize_meeting(meeting_id)
            
            if not summarization_success:
                logger.error(f"Pipeline halted for meeting {meeting_id} due to summarization failure.")
                return
                
            logger.info(f"Pipeline completed successfully for meeting {meeting_id}")
            
        except Exception as e:
            logger.error(f"Unexpected error in processing pipeline for meeting {meeting_id}: {e}")
            logger.error(traceback.format_exc())
        finally:
            db.close()
