from pathlib import Path
import re
import zipfile

import pandas as pd

from .network import _package


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
    :type identifier: str
    :param filepath_csv: path to CSV file containing stimulus set metadata
    :type filepath_csv: Path
    :param filepath_zip: path to ZIP archive containing stimuli
    :type filepath_zip: Path
    :param class_csv: class of CSV file, as defined in the BrainIO specification
    :type class_csv: str
    :param class_zip: class of ZIP archive, as defined in the BrainIO specification
    :type class_zip: str
    :param location_csv: remote location of the CSV file
    :type location_csv: str
    :param location_zip: remote location of the ZIP archive
    :type location_zip: str
    :param catalog_name: name of the BrainIO catalog
    :type catalog_name: str
    :param location_type: location_type of the files, as defined in the BrainIO specification
    :type location_type: str
    """
    _validate(filepath_csv=filepath_csv, filepath_zip=filepath_zip)

    for filepath, class_, location in (
        (filepath_csv, class_csv, location_csv),
        (filepath_zip, class_zip, location_zip),
    ):
        _package(
            identifier=identifier,
            lookup_type="stimulus_set",
            class_=class_,
            filepath=filepath,
            catalog_name=catalog_name,
            location_type=location_type,
            location=location,
            stimulus_set_identifier="",
        )


def _validate(*, filepath_csv: Path, filepath_zip: Path) -> None:
    """Validate the stimulus set and ensure that it follows the BrainIO specification.

    :param filepath_csv: path to CSV file containing stimulus set metadata
    :type filepath_csv: Path
    :param filepath_zip: path to ZIP archive containing stimuli
    :type filepath_zip: Path
    """
    stimulus_set_csv = pd.read_csv(filepath_csv)
    assert all(
        [re.match(r"^[a-z0-9_]+$", column) for column in stimulus_set_csv.columns]
    ), (
        "column headers in the stimulus_set .csv file must contain only lowercase"
        " alphabets, digits, and underscores"
    )
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
        ), (
            "the 'filename' column in the stimulus_set .csv file does not match all the"
            " filenames in the stimulus_set .zip archive"
        )
