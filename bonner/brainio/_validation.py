import re
import zipfile
from pathlib import Path

import netCDF4
import pandas as pd


def validate_catalog(path: Path) -> None:
    assert pd.read_csv(
        path, nrows=1, columns=["column"]
    ), "The column headers of the Catalog CSV file MUST be unique"

    catalog = pd.read_csv(path)
    required_columns = {
        "sha1",
        "lookup_type",
        "identifier",
        "stimulus_set_identifier",
        "location_type",
        "location",
        "class",
    }
    for required_column in required_columns:
        assert (
            required_column in catalog.columns
        ), f"'{required_column} MUST be a column of the Catalog CSV file"

    assert all([re.match(r"^[a-z0-9_]+$", column) for column in catalog.columns]), (
        "The column headers of the Catalog CSV file MUST contain only"
        " lowercase alphabets, digits, and underscores"
    )
    assert catalog["sha1"].is_unique, (
        "The 'sha1' column of the The SHA1 hashes of the files in the Catalog MUST be"
        " unique"
    )
    assert set(catalog["lookup_type"].unique()).issubset(
        {"assembly", "stimulus_set"}
    ), (
        "The values of the 'lookup_type' column of the Catalog CSV file MUST be either"
        " 'assembly' or 'stimulus_set'"
    )


def validate_data_assembly(path: Path) -> None:
    """Validate a Data Assembly."""

    assembly = netCDF4.Dataset(path, "r", format="NETCDF4")

    for attr in {"identifier", "stimulus_set_identifier"}:
        assert (
            attr in assembly.ncattrs()
        ), f"'{attr}' MUST be a global attribute of the Data Assembly"
        # TODO check type of attr: must be string
        # TODO ensure number of non-coordinate variables is one


def validate_stimulus_set(*, path_csv: Path, path_zip: Path) -> None:
    """Validate a Stimulus Set."""

    column_headers = pd.read_csv(path_csv, nrows=1, columns=["column"])
    assert (
        column_headers.is_unique
    ), "The column headers of the Stimulus Set CSV file MUST be unique"

    file_csv = pd.read_csv(path_csv)

    assert all([re.match(r"^[a-z0-9_]+$", column) for column in file_csv.columns]), (
        "The column headers of the Stimulus Set CSV file MUST contain only"
        " lowercase alphabets, digits, and underscores"
    )

    for column in {"stimulus_id", "filename"}:
        assert (
            column in file_csv.columns
        ), f"'{column}' MUST be a column of the Stimulus Set CSV file"

        assert file_csv[column].is_unique, (
            f"The '{column}' column of the Stimulus Set CSV file must contain unique"
            " entries"
        )

    assert all(
        [
            re.match(r"^[a-zA-z0-9]+$", stimulus_id)
            for stimulus_id in file_csv["stimulus_id"]
        ]
    ), (
        "The 'stimulus_id' column of the Stimulus Set CSV file MUST contain"
        " alphanumeric entries"
    )

    with zipfile.ZipFile(path_zip, mode="r") as f:
        assert set(file_csv["filename"]).issubset(
            {zipinfo.filename for zipinfo in f.infolist()}
        ), (
            "All the filepaths in the 'filename' column of the Stimulus Set CSV"
            " file must be present in the Stimulus Set ZIP archive"
        )
