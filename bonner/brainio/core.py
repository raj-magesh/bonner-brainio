from typing import Dict
from pathlib import Path
import os
import shutil
import hashlib
from urllib.parse import urlparse
import zipfile
import subprocess
import re

import pandas as pd
import netCDF4

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
    *,
    catalog_name: str,
    filepath: Path,
) -> pd.DataFrame:
    catalog_dir = BRAINIO_HOME / catalog_name
    catalog_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(filepath, catalog_dir / "catalog.csv")


def fetch(
    *,
    catalog_name: str,
    identifier: str,
    lookup_type: str,
    class_: str,
    check_integrity: bool,
) -> Path:
    metadata = lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type=lookup_type,
        class_=class_,
    )
    assert (
        not metadata.empty
    ), f"{lookup_type} {identifier} not found in catalog {catalog_name}"
    filepath = (
        BRAINIO_HOME
        / catalog_name
        / Path(urlparse(metadata["location"].item()).path).name
    )
    if not filepath.exists():
        _download_file(
            location=metadata["location"].item(),
            filepath=filepath,
            location_type=metadata["location_type"].item(),
        )
    if check_integrity:
        assert metadata["sha1"].item() == _compute_sha1(
            filepath
        ), f"sha1 does not match: {filepath} has been corrupted"
    return filepath


def package_assembly(
    *,
    filepath: Path,
    class_: str,
    catalog_name: str,
    location_type: str,
    location: str,
) -> None:

    _validate_assembly(filepath)
    file = netCDF4.Dataset(filepath, mode="r", format="NETCDF4")

    _send(
        identifier=file.__dict__["identifier"],
        lookup_type="assembly",
        class_=class_,
        filepath=filepath,
        catalog_name=catalog_name,
        location_type=location_type,
        location=location,
        stimulus_set_identifier=file.__dict__["stimulus_set_identifier"],
    )


def package_stimulus_set(
    *,
    identifier: str,
    filepath_csv: Path,
    filepath_zip: Path,
    class_csv: str,
    class_zip: str,
    location_csv: str,
    location_zip: str,
    catalog_name: str,
    location_type: str,
) -> None:

    _validate_stimulus_set(filepath_csv=filepath_csv, filepath_zip=filepath_zip)

    for (filepath, class_, location) in (
        (filepath_csv, class_csv, location_csv),
        (filepath_zip, class_zip, location_zip),
    ):
        _send(
            identifier=identifier,
            lookup_type="stimulus_set",
            class_=class_,
            filepath=filepath,
            catalog_name=catalog_name,
            location_type=location_type,
            location=location,
            stimulus_set_identifier="",
        )


def _send(
    *,
    identifier: str,
    lookup_type: str,
    class_: str,
    filepath: Path,
    catalog_name: str,
    location_type: str,
    location: str,
    stimulus_set_identifier: str = "",
) -> None:

    assert lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type=lookup_type,
        class_=class_,
    ).empty, f"{lookup_type} {identifier} already exists in catalog {catalog_name}"

    sha1 = _compute_sha1(filepath)
    _upload_file(filepath=filepath, location_type=location_type, location=location)

    _catalog_append(
        catalog_name,
        entry={
            "identifier": identifier,
            "lookup_type": lookup_type,
            "class": class_,
            "location_type": location_type,
            "location": location,
            "sha1": sha1,
            "stimulus_set_identifier": stimulus_set_identifier,
        },
    )


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


def _upload_file(*, filepath: Path, location_type: str, location: str) -> None:
    if location_type == "network-storage":
        subprocess.run(
            [
                "rsync",
                "-vzhW",
                "--progress",
                str(filepath),
                location,
            ],
            check=True,
        )
    else:
        raise NotImplementedError(f"location_type {location_type} is unsupported")


def _download_file(*, location: str, filepath: Path, location_type: str) -> None:
    if location_type == "network-storage":
        if not Path(filepath).exists():
            subprocess.run(
                ["rsync", "-vzhW", "--progress", location, str(filepath)], check=True
            )
    else:
        raise NotImplementedError(f"location_type {location_type} is unsupported")


def _compute_sha1(filepath: Path, *, buffer_size: int = 64 * 2**10) -> str:
    sha1 = hashlib.sha1()
    with open(filepath, "rb") as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            sha1.update(buffer)
            buffer = f.read(buffer_size)
    return sha1.hexdigest()


def _validate_assembly(filepath: Path):
    assembly = netCDF4.Dataset(filepath, "r", format="NETCDF4")
    assert (
        "presentation" in assembly.dimensions
    ), "'presentation' must be a dimension in the dataset"
    assert (
        "stimulus_id" in assembly.variables
    ), "'stimulus_id' must be a variable in the dataset"
    assert (
        "presentation" in assembly.variables["stimulus_id"].dimensions
    ), "'stimulus_id' must be a coordinate along the dimension 'presentation'"

    assert (
        "identifier" in assembly.ncattrs()
    ), "'identifier' must be a global attribte in the dataset"
    assert (
        "stimulus_set_identifier" in assembly.ncattrs()
    ), "'stimulus_set_identifier' must be a global attribte in the dataset"


def _validate_stimulus_set(*, filepath_csv: Path, filepath_zip: Path):
    stimulus_set_csv = pd.read_csv(filepath_csv)
    assert all(
        [re.match(r"^[a-z0-9_]+$", column) for column in stimulus_set_csv.columns]
    ), "column headers in the stimulus_set .csv file must contain only lowercase alphabets, digits, and underscores"
    assert (
        "stimulus_id" in stimulus_set_csv.columns
    ), "'stimulus_id' must be a column in the stimulus_set .csv file"
    assert (
        "filename" in stimulus_set_csv.columns
    ), "'filename' must be a column in the stimulus_set .csv file"
    assert stimulus_set_csv[
        "stimulus_id"
    ].is_unique, (
        "'stimulus_id' must be unique across all rows in the stimulus_set .csv file"
    )
    assert all(
        [
            re.match(r"^[a-zA-z0-9]+$", stimulus_id)
            for stimulus_id in stimulus_set_csv["stimulus_id"]
        ]
    ), "the 'stimulus_id' column must be alphanumeric (only alphabets and digits)"

    with zipfile.ZipFile(filepath_zip, mode="r") as f:
        assert set(stimulus_set_csv["filename"]) == set(
            [zipinfo.filename for zipinfo in f.infolist()]
        ), "the 'filename' column in the stimulus_set .csv file does not match all the filenames in the stimulus_set .zip archive"
