"""Private filesystem artifact store used by the local vertical slice."""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .hashing import canonical_json_bytes

_SAFE_ID = re.compile(r"^[a-z]+_[0-9a-f]{32}$")


class LocalArtifactStore:
    def __init__(self, root: str | Path = ".threecraft-data") -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        for name in ("assets", "jobs"):
            directory = self.root / name
            directory.mkdir(exist_ok=True, mode=0o700)
            os.chmod(directory, 0o700)

    @staticmethod
    def new_id(prefix: str) -> str:
        if not prefix.isalpha() or not prefix.islower():
            raise ValueError("ID prefix must contain lowercase letters only")
        return f"{prefix}_{uuid.uuid4().hex}"

    @staticmethod
    def validate_id(value: str) -> str:
        if not _SAFE_ID.fullmatch(value):
            raise ValueError("invalid artifact identifier")
        return value

    def asset_dir(self, asset_id: str) -> Path:
        return self.root / "assets" / self.validate_id(asset_id)

    def job_dir(self, job_id: str) -> Path:
        return self.root / "jobs" / self.validate_id(job_id)

    def create_asset_dir(self, asset_id: str) -> Path:
        path = self.asset_dir(asset_id)
        path.mkdir(parents=False, exist_ok=False, mode=0o700)
        return path

    def create_job_dir(self, job_id: str) -> Path:
        path = self.job_dir(job_id)
        path.mkdir(parents=False, exist_ok=False, mode=0o700)
        return path

    def _atomic_write(self, path: Path, data: bytes) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
        return path

    def write_bytes(self, path: Path, data: bytes) -> Path:
        resolved_parent = path.parent.resolve()
        if self.root != resolved_parent and self.root not in resolved_parent.parents:
            raise ValueError("artifact path escapes the private store")
        return self._atomic_write(path, data)

    def write_json(self, path: Path, value: Any) -> Path:
        return self.write_bytes(path, canonical_json_bytes(value))

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object at {path}")
        return value

    def asset_exists(self, asset_id: str) -> bool:
        return (self.asset_dir(asset_id) / "manifest.json").is_file()

    def job_exists(self, job_id: str) -> bool:
        return (self.job_dir(job_id) / "job.json").is_file()
