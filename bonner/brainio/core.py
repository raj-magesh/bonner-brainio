from typing import Dict
from pathlib import Path
import os
import shutil
import hashlib
from urllib.parse import urlparse
import subprocess

import pandas as pd

BRAINIO_HOME = Path(os.getenv("BRAINIO_HOME", str(Path.home() / "brainio")))


def lookup(
    *, catalog_name: str, identifier: str, lookup_type: str, class_: str
) -> pd.DataFrame:
    catalog = _catalog_load(catalog_name)
    filters = {
        "identifier": catalog["identifier"] == identifier,
        "lookup_type": catalog["lookup_type"] == lookup_type,
        "class": catalog["class"] == class_,
    }
    return catalog.loc[
        filters["identifier"] & filters["lookup_type"] & filters["class"], :
    ]


def import_catalog(
    *, catalog_name: str, filepath: Path,
) -> pd.DataFrame:
    catalog_dir = BRAINIO_HOME / catalog_name
    catalog_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(filepath, catalog_dir / "catalog.csv")


def send(
    *,
    identifier: str,
    lookup_type: str,
    class_: str,
    filepath: Path,
    catalog_name: str,
    location_type: str,
    url: str,
    stimulus_set_identifier: str = ""
) -> None:

    sha1 = _compute_sha1(filepath)
    _upload(filepath=filepath, location_type=location_type, url=url)

    _catalog_append(
        catalog_name,
        entry={
            "identifier": identifier,
            "lookup_type": lookup_type,
            "class": class_,
            "location_type": location_type,
            "location": url,
            "sha1": sha1,
            "stimulus_set_identifier": stimulus_set_identifier,
        },
    )


def fetch(
    *,
    catalog_name: str,
    identifier: str,
    lookup_type: str,
    class_: str,
    check_integrity: bool
) -> Path:
    metadata = lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type=lookup_type,
        class_=class_,
    )
    filepath = (
        BRAINIO_HOME
        / catalog_name
        / Path(urlparse(metadata["location"].item()).path).name
    )
    if not filepath.exists():
        _download(
            url=metadata["location"].item(),
            filepath=filepath,
            location_type=metadata["location_type"].item(),
        )
    if check_integrity:
        assert metadata["sha1"].item() == _compute_sha1(filepath)
    return filepath


def _catalog_initialize(catalog_name: str) -> None:
    catalog = pd.DataFrame(
        data=None,
        columns=(
            "identifier",
            "lookup_type",
            "class",
            "location_type",
            "location",
            "sha1",
            "stimulus_set_identifier",
        ),
    )
    catalog_dir = BRAINIO_HOME / catalog_name
    catalog_dir.mkdir(parents=True, exist_ok=True)
    catalog.to_csv(catalog_dir / "catalog.csv", index=False)


def _catalog_load(catalog_name: str) -> pd.DataFrame:
    path_catalog = BRAINIO_HOME / catalog_name / "catalog.csv"
    if not path_catalog.exists():
        _catalog_initialize(catalog_name)
    return pd.read_csv(path_catalog)


def _catalog_append(catalog_name: str, *, entry: Dict[str, str]) -> pd.DataFrame:
    catalog = _catalog_load(catalog_name)
    catalog = pd.concat([catalog, pd.DataFrame(entry, index=[len(catalog)])])
    catalog.to_csv(BRAINIO_HOME / catalog_name / "catalog.csv", index=False)
    return catalog


def _upload(*, filepath: Path, location_type: str, url: str) -> None:
    if location_type == "network-storage":
        subprocess.run(
            [
                "rsync",
                "-vzhW",
                "--progress",
                str(filepath),
                url,
            ],
            check=True,
        )
    else:
        raise NotImplementedError()


def _download(*, url: str, filepath: Path, location_type: str) -> None:
    if location_type == "network-storage":
        if not Path(filepath).exists():
            subprocess.run(
                ["rsync", "-vzhW", "--progress", url, str(filepath)], check=True
            )
    else:
        raise NotImplementedError()


def _compute_sha1(filepath: Path, *, buffer_size: int = 64 * 2**10) -> str:
    sha1 = hashlib.sha1()
    with open(filepath, "rb") as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            sha1.update(buffer)
            buffer = f.read(buffer_size)
    return sha1.hexdigest()
