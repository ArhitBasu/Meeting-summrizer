import time
from sqlalchemy.orm import Session
from pydantic import ValidationError
from app.models.meeting import (
    Meeting, MeetingStatus, Summary, Decision, ActionItem, Participant, Transcript
)
from app.providers.llm import BaseLLMProvider, get_llm_provider
from app.core.logging import logger

MAX_RETRIES = 1  # Retry once on validation failure; never endless retry


class SummarizationService:
    def __init__(self, db: Session, llm_provider: BaseLLMProvider | None = None):
        self.db = db
        self.llm_provider = llm_provider or get_llm_provider()

    def summarize_meeting(self, meeting_id: int) -> bool:
        """
        Runs LLM summarization for a meeting:
        TRANSCRIBED → SUMMARIZING → COMPLETED (or SUMMARIZATION_FAILED).
        Retries once on Pydantic validation failure.
        Returns True on success, False on failure.
        """
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logger.error(f"meeting_id={meeting_id} not found during summarization.")
            return False

        transcript = self.db.query(Transcript).filter(
            Transcript.meeting_id == meeting_id
        ).first()

        if not transcript or not transcript.text:
            logger.error(f"meeting_id={meeting_id} transcript missing; cannot summarize.")
            meeting.status = MeetingStatus.SUMMARIZATION_FAILED
            self.db.commit()
            return False

        meeting.status = MeetingStatus.SUMMARIZING
        self.db.commit()
        logger.info(f"meeting_id={meeting_id} stage=summarization status=started")

        start_time = time.monotonic()
        attempt = 0

        while attempt <= MAX_RETRIES:
            try:
                structured_data = self.llm_provider.generate_meeting_summary(
                    transcript.text
                )

                # Persist all structured entities
                meeting.title = structured_data.title

                self.db.add(Summary(
                    meeting_id=meeting.id,
                    overview=structured_data.summary,
                    key_points=structured_data.key_points,
                ))

                for dec in structured_data.decisions:
                    self.db.add(Decision(meeting_id=meeting.id, text=dec))

                for item in structured_data.action_items:
                    self.db.add(ActionItem(
                        meeting_id=meeting.id,
                        task=item.task,
                        assignee=item.assignee,
                        deadline=item.deadline,
                    ))

                for name in structured_data.participants:
                    self.db.add(Participant(meeting_id=meeting.id, name=name))

                meeting.status = MeetingStatus.COMPLETED
                self.db.commit()

                duration = time.monotonic() - start_time
                logger.info(
                    f"meeting_id={meeting_id} stage=summarization "
                    f"status=completed duration={duration:.1f}s"
                )
                return True

            except ValidationError as e:
                attempt += 1
                logger.warning(
                    f"meeting_id={meeting_id} stage=summarization "
                    f"validation_error=true attempt={attempt}/{MAX_RETRIES + 1}"
                )
                if attempt > MAX_RETRIES:
                    break  # Fall through to failure path

            except Exception as e:
                logger.error(
                    f"meeting_id={meeting_id} stage=summarization "
                    f"status=failed error={type(e).__name__}: {e}"
                )
                break  # Non-validation errors are not retried

        duration = time.monotonic() - start_time
        logger.error(
            f"meeting_id={meeting_id} stage=summarization "
            f"status=permanently_failed duration={duration:.1f}s"
        )
        meeting.status = MeetingStatus.SUMMARIZATION_FAILED
        self.db.commit()
        return False
