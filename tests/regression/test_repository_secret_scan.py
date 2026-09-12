import subprocess
import sys
from pathlib import Path

import pytest

from scripts.scan_repository_secrets import read_blobs

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def blob_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    data = b"synthetic blob\x00" * 1024
    sha = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=tmp_path, input=data, capture_output=True, check=True,
    ).stdout.decode().strip()
    return tmp_path, sha, data


def test_batch_larger_than_pipe_capacity_completes(blob_repo):
    root, sha, data = blob_repo
    # A separate process bounds the test even if the bidirectional pipe deadlock returns.
    script = """
import sys
from pathlib import Path
from scripts.scan_repository_secrets import read_blobs
count = 0
for sha, data in read_blobs(Path(sys.argv[1]), [sys.argv[2]] * 32768):
    assert sha == sys.argv[2]
    assert data == b"synthetic blob\\x00" * 1024
    count += 1
assert count == 32768
"""
    subprocess.run(
        [sys.executable, "-c", script, str(root), sha],
        cwd=ROOT, check=True, capture_output=True, timeout=30,
    )


def test_empty_batch(blob_repo):
    root, _, _ = blob_repo
    assert list(read_blobs(root, [])) == []


def test_missing_object_fails_closed(blob_repo):
    root, _, _ = blob_repo
    with pytest.raises(RuntimeError, match="Unexpected"):
        list(read_blobs(root, ["0" * 40]))


def test_early_close_reaps_child(blob_repo):
    root, sha, data = blob_repo
    iterator = read_blobs(root, [sha, sha])
    assert next(iterator) == (sha, data)
    process = iterator.gi_frame.f_locals["process"]
    iterator.close()
    assert process.poll() is not None
