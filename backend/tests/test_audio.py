import pytest
from app.services.audio import AudioStorageService
from fastapi import UploadFile
import io
from app.core.config import settings

class MockUploadFile(UploadFile):
    def __init__(self, filename, content):
        super().__init__(filename=filename, file=io.BytesIO(content))
        self.filename = filename

def test_validate_file_success():
    file = MockUploadFile("meeting.mp3", b"test audio content")
    AudioStorageService.validate_file(file)

def test_validate_file_invalid_extension():
    file = MockUploadFile("meeting.pdf", b"test pdf content")
    with pytest.raises(ValueError, match="Unsupported file format"):
        AudioStorageService.validate_file(file)

def test_validate_file_too_large(monkeypatch):
    monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 0.000001) 
    file = MockUploadFile("meeting.mp3", b"this is slightly larger than the mocked max size")
    with pytest.raises(ValueError, match="File size exceeds maximum limit"):
        AudioStorageService.validate_file(file)
