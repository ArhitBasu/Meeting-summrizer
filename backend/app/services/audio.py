import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings
from app.core.logging import logger

class AudioStorageService:
    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a'}

    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        """
        Strip any path components from a user-supplied filename to prevent
        path-traversal attacks (e.g., '../../etc/passwd.mp3').
        Only the base filename is kept.
        """
        return Path(filename).name

    @classmethod
    def validate_file(cls, file: UploadFile) -> None:
        """Raises ValueError if the file type or size is unacceptable."""
        safe_name = cls._sanitize_filename(file.filename or "")
        if not any(safe_name.lower().endswith(ext) for ext in cls.ALLOWED_EXTENSIONS):
            raise ValueError("Unsupported file format. Allowed: .mp3, .wav, .m4a")

        # Check size without loading the entire file into memory
        file.file.seek(0, 2)
        size_mb = file.file.tell() / (1024 * 1024)
        file.file.seek(0)

        if size_mb == 0:
            raise ValueError("Uploaded file is empty.")

        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File size ({size_mb:.1f} MB) exceeds the maximum allowed "
                f"limit of {settings.MAX_FILE_SIZE_MB} MB."
            )

    @classmethod
    def save_file(cls, file: UploadFile) -> str:
        """
        Saves the file to the configured storage directory with a UUID-prefixed
        name to prevent collisions. Returns the absolute file path.
        """
        safe_name = cls._sanitize_filename(file.filename or "audio.bin")
        unique_filename = f"{uuid.uuid4()}_{safe_name}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"Saved audio file: {unique_filename}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            raise RuntimeError("Could not save audio file to storage.")

    @classmethod
    def delete_file(cls, file_path: str) -> None:
        """Silently removes a stored audio file; errors are logged but not raised."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted audio file: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Failed to delete audio file '{file_path}': {e}")
