"""TODO add docstring."""

__all__: list[str] = []

import hashlib
import re
import zipfile
from pathlib import Path

import netCDF4
import pandas as pd


def validate_catalog(path: Path) -> None:
    """Validate a BrainIO Catalog.

    Ensures that the Catalog complies with the BrainIO specification.

    :param path: path to the Catalog CSV file
    """
    assert pd.read_csv(
        path, nrows=1, columns=["column"]
    ).is_unique, f"The column headers of the Catalog CSV file {path} MUST be unique"

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
        ), f"'{required_column}' MUST be a column of the Catalog CSV file {path}"

    for column in catalog.columns:
        assert re.match(r"^[a-z0-9_]+$", column), (
            f"The column header '{column}' of the Catalog CSV file {path} MUST contain"
            " only lowercase alphabets, digits, and underscores"
        )

    # TODO check that the identifier column, stimulus_set_identifier column contains strings
    # TODO check that the SHA1 column contains valid SHA1 hashes
    # TODO check that the location column contains valid URLs
    # TODO check that no Data Assembly is repeated
    # TODO check that no Stimulus Set is repeated
    # TODO check that each Stimulus Set has two entries
    # TODO check that each Data Assembly has two entries
    # TODO check that the {identifier, stimulus_identifier} columns of a DataAssembly match its internal global attributes
    # TODO validate each Data Assembly and Stimulus Set

    assert catalog["sha1"].is_unique, (
        f"The 'sha1' column of the Catalog CSV file {path} MUST contain unique entries"
        " unique"
    )
    assert set(catalog["lookup_type"].unique()).issubset(
        {"assembly", "stimulus_set"}
    ), (
        f"The values of the 'lookup_type' column of the Catalog CSV file {path} MUST be"
        " either 'assembly' or 'stimulus_set'"
    )


def validate_data_assembly(path: Path) -> None:
    """Validate a BrainIO Data Assembly.

    Ensures that the Data Assembly complies with the BrainIO specification.

    :param path: path to the Data Assembly netCDF-4 file
    """

    assembly = netCDF4.Dataset(path, "r", format="NETCDF4")

    for required_attribute in {"identifier", "stimulus_set_identifier"}:
        assert required_attribute in assembly.ncattrs().__dict__, (
            f"'{required_attribute}' MUST be a global attribute of the Data Assembly"
            f" {path}"
        )

        assert isinstance(assembly.ncattrs().__dict__[required_attribute], str), (
            f"The '{required_attribute} global attribute of the Data Assembly"
            f" {path} MUST be a string"
        )

        # TODO ensure number of non-coordinate variables is one


def validate_stimulus_set(*, path_csv: Path, path_zip: Path) -> None:
    """Validate a BrainIO Stimulus Set.

    Ensures that the Stimulus Set complies with the BrainIO specification.

    :param path_csv: path to the Stimulus Set CSV file
    :param path_zip: path to the Stimulus Set ZIP file
    """
    column_headers = pd.read_csv(path_csv, nrows=1, columns=["column"])
    assert (
        column_headers.is_unique
    ), f"The column headers of the Stimulus Set CSV file {path_csv} MUST be unique"

    file_csv = pd.read_csv(path_csv)
    for column in {"stimulus_id", "filename"}:
        assert (
            column in file_csv.columns
        ), f"'{column}' MUST be a column of the Stimulus Set CSV file {path_csv}"

        assert file_csv[column].is_unique, (
            f"The '{column}' column of the Stimulus Set CSV file {path_csv} MUST"
            " contain unique entries"
        )

    for column in file_csv.columns:
        assert re.match(r"^[a-z0-9_]+$", column), (
            f"The column header '{column}' of the Stimulus Set CSV file {path_csv} MUST"
            " contain only lowercase alphabets, digits, and underscores"
        )

    for stimulus_id in file_csv["stimulus_id"]:
        assert re.match(r"^[a-zA-z0-9]+$", stimulus_id), (
            f"The {stimulus_id} entry in the 'stimulus_id' column of the Stimulus Set"
            f" CSV file {path_csv} MUST be alphanumeric"
        )

    with zipfile.ZipFile(path_zip, mode="r") as f:
        assert set(file_csv["filename"]).issubset(
            {zipinfo.filename for zipinfo in f.infolist()}
        ), (
            "All the filepaths in the 'filename' column of the Stimulus Set CSV file"
            f" {path_csv} MUST be present in the Stimulus Set ZIP archive {path_zip}"
        )


def compute_sha1(path: Path) -> str:
    """Compute the SHA1 hash of a file.

    :param path: path to the file
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
