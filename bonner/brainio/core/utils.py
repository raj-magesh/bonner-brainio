from pathlib import Path
import os
import hashlib

BRAINIO_HOME = Path(os.getenv("BRAINIO_HOME", str(Path.home() / "brainio")))


def _compute_sha1(filepath: Path, *, buffer_size: int = 64 * 2**10) -> str:
    sha1 = hashlib.sha1()
    with open(filepath, "rb") as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            sha1.update(buffer)
            buffer = f.read(buffer_size)
    return sha1.hexdigest()
