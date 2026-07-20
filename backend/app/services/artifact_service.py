"""
------------------------------------------------------------------------------
CorrelAI

Artifact Service

Handles basic artifact storage and file-system operations for uploaded files.

------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class ArtifactService:
    """
    Minimal artifact storage helper.

    This service is intentionally lightweight for v0.1. It provides a simple
    filesystem-backed place to store uploaded artifacts in a container-friendly
    way without introducing a database yet.
    """

    def __init__(self, root_dir: Path | str | None = None) -> None:
        self.root_dir = Path(root_dir) if root_dir is not None else Path("artifacts")
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def ensure_root(self) -> Path:
        """
        Ensure the artifact root directory exists.

        Returns:
            The root directory path.
        """
        self.root_dir.mkdir(parents=True, exist_ok=True)
        return self.root_dir

    def get_artifact_path(self, filename: str) -> Path:
        """
        Build a safe storage path for an artifact.

        Args:
            filename: Original filename or artifact name.

        Returns:
            A path under the artifact root directory.
        """
        safe_name = Path(filename).name
        unique_name = f"{uuid4()}_{safe_name}"
        return self.root_dir / unique_name

    def save_bytes(self, filename: str, data: bytes) -> Path:
        """
        Save raw bytes to the artifact store.

        Args:
            filename: Original filename.
            data: File content as bytes.

        Returns:
            The saved artifact path.
        """
        path = self.get_artifact_path(filename)
        path.write_bytes(data)
        return path

    def save_text(self, filename: str, content: str, encoding: str = "utf-8") -> Path:
        """
        Save text content to the artifact store.

        Args:
            filename: Original filename.
            content: Text content.
            encoding: Encoding to use when writing.

        Returns:
            The saved artifact path.
        """
        path = self.get_artifact_path(filename)
        path.write_text(content, encoding=encoding)
        return path

    def read_bytes(self, path: Path | str) -> bytes:
        """
        Read bytes from a stored artifact.

        Args:
            path: Artifact path.

        Returns:
            File content as bytes.
        """
        return Path(path).read_bytes()

    def delete(self, path: Path | str) -> None:
        """
        Delete a stored artifact if it exists.

        Args:
            path: Artifact path.
        """
        artifact_path = Path(path)
        if artifact_path.exists():
            artifact_path.unlink()

    def exists(self, path: Path | str) -> bool:
        """
        Check whether a stored artifact exists.

        Args:
            path: Artifact path.

        Returns:
            True if the file exists.
        """
        return Path(path).exists()