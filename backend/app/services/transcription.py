import time
from sqlalchemy.orm import Session
from app.models.meeting import Meeting, MeetingStatus, Transcript
from app.providers.asr import BaseASRProvider, get_asr_provider
from app.core.logging import logger


class TranscriptionService:
    def __init__(self, db: Session, asr_provider: BaseASRProvider | None = None):
        self.db = db
        self.asr_provider = asr_provider or get_asr_provider()

    def transcribe_meeting(self, meeting_id: int, file_path: str) -> bool:
        """
        Runs transcription for a meeting:
        UPLOADED → TRANSCRIBING → TRANSCRIBED (or TRANSCRIPTION_FAILED).
        Returns True on success, False on failure.
        """
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logger.error(f"meeting_id={meeting_id} not found during transcription.")
            return False

        meeting.status = MeetingStatus.TRANSCRIBING
        self.db.commit()
        logger.info(f"meeting_id={meeting_id} stage=transcription status=started")

        start_time = time.monotonic()
        try:
            transcript_text = self.asr_provider.transcribe(file_path)

            if not transcript_text or not transcript_text.strip():
                raise ValueError("ASR provider returned an empty transcript.")

            transcript = Transcript(meeting_id=meeting.id, text=transcript_text)
            self.db.add(transcript)
            meeting.status = MeetingStatus.TRANSCRIBED
            self.db.commit()

            duration = time.monotonic() - start_time
            logger.info(
                f"meeting_id={meeting_id} stage=transcription "
                f"status=completed duration={duration:.1f}s"
            )
            return True

        except Exception as e:
            duration = time.monotonic() - start_time
            logger.error(
                f"meeting_id={meeting_id} stage=transcription "
                f"status=failed duration={duration:.1f}s error={type(e).__name__}"
            )
            meeting.status = MeetingStatus.TRANSCRIPTION_FAILED
            self.db.commit()
            return False
