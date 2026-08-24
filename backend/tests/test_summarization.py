import pytest
from unittest.mock import MagicMock
from app.services.summarization import SummarizationService
from app.models.meeting import Meeting, MeetingStatus, Transcript
from app.providers.llm import StructuredMeetingSummary, ActionItemParsed
from pydantic import ValidationError

def test_summarize_meeting_success(monkeypatch):
    mock_db = MagicMock()
    mock_meeting = Meeting(id=1, status=MeetingStatus.TRANSCRIBED)
    mock_transcript = Transcript(id=1, meeting_id=1, text="Test transcript text")
    
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_meeting, mock_transcript]

    mock_structured_data = StructuredMeetingSummary(
        title="Test Meeting",
        summary="A test summary",
        key_points=["Point 1"],
        decisions=["Dec 1"],
        action_items=[ActionItemParsed(task="Test Task")],
        participants=["John"]
    )
    
    mock_provider = MagicMock()
    mock_provider.generate_meeting_summary.return_value = mock_structured_data
    monkeypatch.setattr('app.services.summarization.get_llm_provider', lambda: mock_provider)

    service = SummarizationService(db=mock_db)
    success = service.summarize_meeting(1)

    assert success is True
    assert mock_meeting.status == MeetingStatus.COMPLETED

def test_summarize_meeting_retry_failure(monkeypatch):
    mock_db = MagicMock()
    mock_meeting = Meeting(id=1, status=MeetingStatus.TRANSCRIBED)
    mock_transcript = Transcript(id=1, meeting_id=1, text="Test transcript text")
    
    # Need to return these multiple times due to retries
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_meeting, mock_transcript] * 3

    mock_provider = MagicMock()
    # Simulate a validation error every time
    mock_provider.generate_meeting_summary.side_effect = ValidationError.from_exception_data("error", line_errors=[])
    monkeypatch.setattr('app.services.summarization.get_llm_provider', lambda: mock_provider)

    service = SummarizationService(db=mock_db)
    success = service.summarize_meeting(1)

    assert success is False
    assert mock_meeting.status == MeetingStatus.SUMMARIZATION_FAILED
    # Should have tried twice (initial + 1 retry)
    assert mock_provider.generate_meeting_summary.call_count == 2
