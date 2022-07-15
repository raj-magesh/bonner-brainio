from typing import Tuple
from pathlib import Path
import shutil
import zipfile
import re

import pandas as pd

from .core import BRAINIO_HOME, lookup, fetch, send


def package(
    *,
    identifier: str,
    stimulus_set: pd.DataFrame,
    stimulus_dir: Path,
    catalog_name: str,
    location_type: str,
    location: str,
) -> None:

    assert all([lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type="stimulus_set",
        class_=filetype
    ).empty for filetype in ("csv", "zip")]), f"stimulus_set {identifier} already exists in catalog {catalog_name}"

    _verify(stimulus_set=stimulus_set, stimulus_dir=stimulus_dir)

    filepaths = {
        "csv": create_csv(
            identifier=identifier,
            stimulus_set=stimulus_set,
            catalog_name=catalog_name,
        ),
        "zip": create_zip(
            identifier=identifier,
            stimulus_set=stimulus_set,
            stimulus_dir=stimulus_dir,
            catalog_name=catalog_name,
        ),
    }

    for filetype, filepath in filepaths.items():
        send(
            identifier=identifier,
            lookup_type="stimulus_set",
            class_=filetype,
            filepath=filepath,
            catalog_name=catalog_name,
            location_type=location_type,
            url=f"{location}/{filepath.name}",
            stimulus_set_identifier="",
        )


def _verify(*, stimulus_set: pd.DataFrame, stimulus_dir: Path) -> None:
    assert all([re.match(r"^[a-z0-9_]+$", column) for column in stimulus_set.columns])
    assert "stimulus_id" in stimulus_set.columns
    assert "filename" in stimulus_set.columns
    assert stimulus_set["stimulus_id"].is_unique
    assert all(
        [re.match(r"^[a-zA-z0-9]+$", stimulus_id) for stimulus_id in stimulus_set["stimulus_id"]]
    )
    for filename in stimulus_set["filename"]:
        assert (stimulus_dir / filename).exists()


def create_csv(*, identifier: str, stimulus_set: pd.DataFrame, catalog_name: str) -> Path:
    filepath = BRAINIO_HOME / catalog_name / f"{identifier}.csv"
    stimulus_set.to_csv(filepath, index=False)
    return filepath


def create_zip(
    *, identifier: str, stimulus_set: pd.DataFrame, stimulus_dir: Path, catalog_name: str
) -> Path:
    filepath_zip = BRAINIO_HOME / catalog_name / f"{identifier}.zip"
    with zipfile.ZipFile(filepath_zip, "w") as zip:
        for filename in stimulus_set["filename"]:
            zip.write(stimulus_dir / filename, arcname=filename)
    return filepath_zip


def load(
    catalog_name: str, identifier: str, check_integrity: bool = True
) -> Tuple[pd.DataFrame, Path]:
    filepaths = {
        filetype: fetch(
            catalog_name=catalog_name,
            identifier=identifier,
            lookup_type="stimulus_set",
            class_=filetype,
            check_integrity=check_integrity,
        )
        for filetype in ("csv", "zip")
    }

    csv = pd.read_csv(filepaths["csv"])

    stimuli_dir = BRAINIO_HOME / catalog_name / f"{identifier}"

    if not all([(stimuli_dir / subpath).exists() for subpath in csv["filename"]]):
        if stimuli_dir.exists():
            shutil.rmtree(stimuli_dir)
        stimuli_dir.mkdir(parents=True)
        with zipfile.ZipFile(filepaths["zip"], "r") as f:
            f.extractall(stimuli_dir)

    return csv, stimuli_dir
