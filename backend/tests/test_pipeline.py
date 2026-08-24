import pytest
from unittest.mock import MagicMock
from app.services.transcription import TranscriptionService
from app.services.summarization import SummarizationService
from app.models.meeting import Meeting, MeetingStatus, Transcript
from app.providers.llm import StructuredMeetingSummary, ActionItemParsed
from pydantic import ValidationError


# ── Transcription ────────────────────────────────────────────────────────────

class TestTranscriptionService:
    def _make_db(self, meeting):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = meeting
        return mock_db

    def test_transcription_success(self):
        meeting = Meeting(id=1, status=MeetingStatus.UPLOADED)
        db = self._make_db(meeting)

        provider = MagicMock()
        provider.transcribe.return_value = "This is the transcript."

        service = TranscriptionService(db=db, asr_provider=provider)
        result = service.transcribe_meeting(1, "fake.mp3")

        assert result is True
        assert meeting.status == MeetingStatus.TRANSCRIBED
        assert db.add.called

    def test_transcription_provider_error(self):
        meeting = Meeting(id=1, status=MeetingStatus.UPLOADED)
        db = self._make_db(meeting)

        provider = MagicMock()
        provider.transcribe.side_effect = RuntimeError("API timeout")

        service = TranscriptionService(db=db, asr_provider=provider)
        result = service.transcribe_meeting(1, "fake.mp3")

        assert result is False
        assert meeting.status == MeetingStatus.TRANSCRIPTION_FAILED

    def test_transcription_empty_transcript(self):
        meeting = Meeting(id=1, status=MeetingStatus.UPLOADED)
        db = self._make_db(meeting)

        provider = MagicMock()
        provider.transcribe.return_value = "   "  # Whitespace only

        service = TranscriptionService(db=db, asr_provider=provider)
        result = service.transcribe_meeting(1, "fake.mp3")

        assert result is False
        assert meeting.status == MeetingStatus.TRANSCRIPTION_FAILED

    def test_meeting_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        provider = MagicMock()
        service = TranscriptionService(db=db, asr_provider=provider)
        result = service.transcribe_meeting(999, "fake.mp3")

        assert result is False
        provider.transcribe.assert_not_called()


# ── Summarization ─────────────────────────────────────────────────────────────

def _make_valid_summary(**kwargs) -> StructuredMeetingSummary:
    defaults = dict(
        title="Test Meeting",
        summary="A test summary.",
        key_points=["Point 1"],
        decisions=["Decision 1"],
        action_items=[ActionItemParsed(task="Do something", assignee="Alice", deadline="Friday")],
        participants=["Alice"],
    )
    defaults.update(kwargs)
    return StructuredMeetingSummary(**defaults)


class TestSummarizationService:
    def _make_db(self, meeting, transcript):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            meeting, transcript
        ]
        return db

    def test_summarization_success(self):
        meeting = Meeting(id=1, status=MeetingStatus.TRANSCRIBED)
        transcript = Transcript(id=1, meeting_id=1, text="Transcript text.")
        db = self._make_db(meeting, transcript)

        provider = MagicMock()
        provider.generate_meeting_summary.return_value = _make_valid_summary()

        service = SummarizationService(db=db, llm_provider=provider)
        result = service.summarize_meeting(1)

        assert result is True
        assert meeting.status == MeetingStatus.COMPLETED
        assert meeting.title == "Test Meeting"

    def test_null_assignee_and_deadline_persisted(self):
        meeting = Meeting(id=1, status=MeetingStatus.TRANSCRIBED)
        transcript = Transcript(id=1, meeting_id=1, text="Transcript text.")
        db = self._make_db(meeting, transcript)

        provider = MagicMock()
        provider.generate_meeting_summary.return_value = _make_valid_summary(
            action_items=[ActionItemParsed(task="Do something", assignee=None, deadline=None)]
        )

        service = SummarizationService(db=db, llm_provider=provider)
        result = service.summarize_meeting(1)

        assert result is True
        # Verify ActionItem was added with null fields
        added_items = [
            call_args[0][0]
            for call_args in db.add.call_args_list
            if hasattr(call_args[0][0], "assignee")
        ]
        assert any(item.assignee is None for item in added_items)

    def test_validation_error_retries_once_then_fails(self):
        meeting = Meeting(id=1, status=MeetingStatus.TRANSCRIBED)
        transcript = Transcript(id=1, meeting_id=1, text="Transcript text.")
        # Return meeting+transcript for each retry attempt
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            meeting, transcript, meeting, transcript
        ]

        provider = MagicMock()
        # Simulate Pydantic validation error on every call
        provider.generate_meeting_summary.side_effect = ValidationError.from_exception_data(
            "StructuredMeetingSummary", []
        )

        service = SummarizationService(db=db, llm_provider=provider)
        result = service.summarize_meeting(1)

        assert result is False
        assert meeting.status == MeetingStatus.SUMMARIZATION_FAILED
        # Exactly 2 attempts: initial + 1 retry
        assert provider.generate_meeting_summary.call_count == 2

    def test_general_exception_does_not_retry(self):
        meeting = Meeting(id=1, status=MeetingStatus.TRANSCRIBED)
        transcript = Transcript(id=1, meeting_id=1, text="Transcript text.")
        db = self._make_db(meeting, transcript)

        provider = MagicMock()
        provider.generate_meeting_summary.side_effect = RuntimeError("Connection failed")

        service = SummarizationService(db=db, llm_provider=provider)
        result = service.summarize_meeting(1)

        assert result is False
        assert meeting.status == MeetingStatus.SUMMARIZATION_FAILED
        # Should NOT retry on generic errors
        assert provider.generate_meeting_summary.call_count == 1

    def test_missing_transcript_fails_gracefully(self):
        meeting = Meeting(id=1, status=MeetingStatus.TRANSCRIBED)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [meeting, None]

        provider = MagicMock()
        service = SummarizationService(db=db, llm_provider=provider)
        result = service.summarize_meeting(1)

        assert result is False
        assert meeting.status == MeetingStatus.SUMMARIZATION_FAILED
        provider.generate_meeting_summary.assert_not_called()


# ── State machine ─────────────────────────────────────────────────────────────

class TestStateMachineTransitions:
    """
    Verify the complete happy-path state machine:
    UPLOADED → TRANSCRIBING → TRANSCRIBED → SUMMARIZING → COMPLETED
    """

    def test_full_happy_path_states(self):
        states_observed = []
        meeting = Meeting(id=1, status=MeetingStatus.UPLOADED)
        transcript = Transcript(id=1, meeting_id=1, text="Full transcript text here.")

        # Track state changes via a property mock
        original_setter = Meeting.status.fset
        committed_statuses = []

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            meeting,  # TranscriptionService lookup
            meeting,  # SummarizationService lookup
            transcript,  # SummarizationService transcript lookup
        ]

        def track_commit():
            committed_statuses.append(meeting.status)

        db.commit.side_effect = track_commit

        asr = MagicMock()
        asr.transcribe.return_value = "Full transcript text here."

        llm = MagicMock()
        llm.generate_meeting_summary.return_value = _make_valid_summary()

        # Run transcription
        t_service = TranscriptionService(db=db, asr_provider=asr)
        t_result = t_service.transcribe_meeting(1, "audio.mp3")

        assert t_result is True
        assert MeetingStatus.TRANSCRIBED in committed_statuses

        # Run summarization
        s_service = SummarizationService(db=db, llm_provider=llm)
        s_result = s_service.summarize_meeting(1)

        assert s_result is True
        assert MeetingStatus.COMPLETED in committed_statuses
