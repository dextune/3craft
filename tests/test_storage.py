from __future__ import annotations

import os
import stat

import pytest

from threecraft.storage import LocalArtifactStore


def _mode(path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_store_enforces_private_permissions_and_atomic_files(tmp_path) -> None:
    root = tmp_path / "data"
    root.mkdir(mode=0o755)
    (root / "assets").mkdir(mode=0o755)
    (root / "jobs").mkdir(mode=0o755)
    os.chmod(root, 0o755)
    os.chmod(root / "assets", 0o755)
    os.chmod(root / "jobs", 0o755)

    store = LocalArtifactStore(root)
    assert _mode(root) == 0o700
    assert _mode(root / "assets") == 0o700
    assert _mode(root / "jobs") == 0o700

    asset_id = store.new_id("ast")
    asset_dir = store.create_asset_dir(asset_id)
    artifact = store.write_bytes(asset_dir / "source.png", b"private")
    assert _mode(asset_dir) == 0o700
    assert _mode(artifact) == 0o600
    assert artifact.read_bytes() == b"private"


def test_store_rejects_invalid_ids_and_path_escape(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "data")
    with pytest.raises(ValueError, match="invalid artifact identifier"):
        store.asset_dir("../outside")
    with pytest.raises(ValueError, match="escapes"):
        store.write_bytes(tmp_path / "outside.bin", b"no")
