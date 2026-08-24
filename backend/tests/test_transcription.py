import pytest
from unittest.mock import MagicMock
from app.services.transcription import TranscriptionService
from app.models.meeting import Meeting, MeetingStatus

def test_transcribe_meeting_success(monkeypatch):
    mock_db = MagicMock()
    mock_meeting = Meeting(id=1, status=MeetingStatus.UPLOADED)
    mock_db.query().filter().first.return_value = mock_meeting

    mock_provider = MagicMock()
    mock_provider.transcribe.return_value = "This is a test transcript."
    monkeypatch.setattr('app.services.transcription.get_asr_provider', lambda: mock_provider)

    service = TranscriptionService(db=mock_db)
    success = service.transcribe_meeting(1, "fake_path.mp3")

    assert success is True
    assert mock_meeting.status == MeetingStatus.TRANSCRIBED
    assert mock_db.add.called
    assert mock_db.commit.called

def test_transcribe_meeting_provider_failure(monkeypatch):
    mock_db = MagicMock()
    mock_meeting = Meeting(id=1, status=MeetingStatus.UPLOADED)
    mock_db.query().filter().first.return_value = mock_meeting

    mock_provider = MagicMock()
    mock_provider.transcribe.side_effect = Exception("API Error")
    monkeypatch.setattr('app.services.transcription.get_asr_provider', lambda: mock_provider)

    service = TranscriptionService(db=mock_db)
    success = service.transcribe_meeting(1, "fake_path.mp3")

    assert success is False
    assert mock_meeting.status == MeetingStatus.TRANSCRIPTION_FAILED
