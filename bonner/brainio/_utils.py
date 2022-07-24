"""TODO add docstring."""

__all__: list[str] = []

import hashlib
import os
from pathlib import Path

HOME = Path(os.getenv("BONNER_BRAINIO_HOME", str(Path.home() / "brainio")))


def compute_sha1(path: Path) -> str:
    """Compute the SHA1 hash of a file.

    :param filepath: path to file
    :return: SHA1 hash of the file
    """
    buffer_size = 64 * 2**10
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            sha1.update(buffer)
            buffer = f.read(buffer_size)
    return sha1.hexdigest()
