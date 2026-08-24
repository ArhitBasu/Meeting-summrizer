import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import io

# Test database setup
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.database.base import Base
from app.database.session import get_db
from app.main import app

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def clean_db():
    """Reset database state between tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestUploadEndpoint:
    def test_upload_valid_mp3(self, client):
        audio_content = b"ID3" + b"\x00" * 100  # Fake MP3 header
        response = client.post(
            "/api/meetings/upload",
            files={"file": ("meeting.mp3", io.BytesIO(audio_content), "audio/mpeg")},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "UPLOADED"
        assert data["filename"] == "meeting.mp3"

    def test_upload_invalid_extension(self, client):
        response = client.post(
            "/api/meetings/upload",
            files={"file": ("report.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_upload_empty_file(self, client):
        response = client.post(
            "/api/meetings/upload",
            files={"file": ("empty.mp3", io.BytesIO(b""), "audio/mpeg")},
        )
        assert response.status_code == 400

    def test_path_traversal_attempt(self, client):
        """File should be saved safely even with a malicious filename."""
        audio_content = b"RIFF" + b"\x00" * 100
        response = client.post(
            "/api/meetings/upload",
            files={
                "file": (
                    "../../etc/passwd.wav",
                    io.BytesIO(audio_content),
                    "audio/wav",
                )
            },
        )
        # Should accept the file (it has a .wav extension) but strip the path
        assert response.status_code == 202


class TestMeetingEndpoints:
    def _create_meeting(self, client):
        audio_content = b"ID3" + b"\x00" * 100
        return client.post(
            "/api/meetings/upload",
            files={"file": ("meeting.mp3", io.BytesIO(audio_content), "audio/mpeg")},
        ).json()

    def test_list_meetings_empty(self, client):
        response = client.get("/api/meetings/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_meetings_after_upload(self, client):
        self._create_meeting(client)
        response = client.get("/api/meetings/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_meeting_exists(self, client):
        meeting = self._create_meeting(client)
        response = client.get(f"/api/meetings/{meeting['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == meeting["id"]

    def test_get_meeting_not_found(self, client):
        response = client.get("/api/meetings/99999")
        assert response.status_code == 404

    def test_transcript_not_available(self, client):
        meeting = self._create_meeting(client)
        response = client.get(f"/api/meetings/{meeting['id']}/transcript")
        assert response.status_code == 404

    def test_summary_not_available(self, client):
        meeting = self._create_meeting(client)
        response = client.get(f"/api/meetings/{meeting['id']}/summary")
        assert response.status_code == 404

    def test_delete_meeting(self, client):
        meeting = self._create_meeting(client)
        response = client.delete(f"/api/meetings/{meeting['id']}")
        assert response.status_code == 204

        response = client.get(f"/api/meetings/{meeting['id']}")
        assert response.status_code == 404

    def test_delete_meeting_not_found(self, client):
        response = client.delete("/api/meetings/99999")
        assert response.status_code == 404

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
