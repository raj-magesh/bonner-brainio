from pathlib import Path
import os
import hashlib

BONNER_BRAINIO_HOME = Path(os.getenv("BRAINIO_HOME", str(Path.home() / "brainio")))


def _compute_sha1(filepath: Path) -> str:
    """Compute the SHA1 hash of a file.

    :param filepath: path to file
    :type filepath: Path
    :return: SHA1 hash of the file
    :rtype: str
    """
    buffer_size = 64 * 2**10
    sha1 = hashlib.sha1()
    with open(filepath, "rb") as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            sha1.update(buffer)
            buffer = f.read(buffer_size)
    return sha1.hexdigest()
