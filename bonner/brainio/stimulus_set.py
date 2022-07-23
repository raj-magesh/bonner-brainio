"""TODO add docstring."""

__all__: list[str] = ["package", "load"]

import re
import zipfile
from pathlib import Path

import pandas as pd

from ._network import send


class StimulusSet:
    def __init__(self, identifier: str, path_csv: Path, path_zip: Path) -> None:
        self.identifier = identifier
        self._path_csv = path_csv
        self._path_zip = path_zip

    def _validate(self) -> None:
        """Validate the Stimulus Set"""

        assert pd.read_csv(
            nrows=1, columns=["column"]
        ), "column headers in the Stimulus Set CSV file MUST be unique"

        file_csv = pd.read_csv(self._path_csv)

        assert all(
            [re.match(r"^[a-z0-9_]+$", column) for column in file_csv.columns]
        ), (
            "column headers in the Stimulus Set CSV file MUST contain only lowercase"
            " alphabets, digits, and underscores"
        )
        assert (
            "stimulus_id" in file_csv.columns
        ), "'stimulus_id' MUST be a column in the Stimulus Set CSV file"
        assert (
            "filename" in file_csv.columns
        ), "'filename' MUST be a column in the Stimulus Set CSV file"
        assert file_csv[
            "stimulus_id"
        ].is_unique, (
            "'stimulus_id' must be unique across all rows in the Stimulus Set CSV file"
        )
        assert all(
            [
                re.match(r"^[a-zA-z0-9]+$", stimulus_id)
                for stimulus_id in file_csv["stimulus_id"]
            ]
        ), "the 'stimulus_id' column must be alphanumeric (only alphabets and digits)"

        with zipfile.ZipFile(self.path_zip, mode="r") as f:
            assert set(file_csv["filename"]).issubset(
                {zipinfo.filename for zipinfo in f.infolist()}
            ), (
                "the 'filename' column in the stimulus_set .csv file does not match all"
                " the filenames in the stimulus_set .zip archive"
            )


def package(
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
    """Package a stimulus set.

    :param identifier: identifier of the file, as defined in the BrainIO specification
    :param filepath_csv: path to CSV file containing stimulus set metadata
    :param filepath_zip: path to ZIP archive containing stimuli
    :param class_csv: class of CSV file, as defined in the BrainIO specification
    :param class_zip: class of ZIP archive, as defined in the BrainIO specification
    :param location_csv: remote location of the CSV file
    :param location_zip: remote location of the ZIP archive
    :param catalog_name: name of the BrainIO catalog
    :param location_type: location_type of the files, as defined in the BrainIO specification
    """
    _validate(filepath_csv=filepath_csv, filepath_zip=filepath_zip)

    for filepath, class_, location in (
        (filepath_csv, class_csv, location_csv),
        (filepath_zip, class_zip, location_zip),
    ):
        send(
            identifier=identifier,
            lookup_type="stimulus_set",
            class_=class_,
            filepath=filepath,
            catalog_name=catalog_name,
            location_type=location_type,
            location=location,
            stimulus_set_identifier="",
        )
