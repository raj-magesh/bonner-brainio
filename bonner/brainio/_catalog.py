import shutil
from typing import TYPE_CHECKING, Mapping

import pandas as pd

from ._utils import _BONNER_BRAINIO_HOME

if TYPE_CHECKING:
    from pathlib import Path


def _import(
    *,
    catalog_name: str,
    filepath: Path,
) -> None:
    """Import a catalog from a file.

    :param catalog_name: name of the BrainIO catalog
    :param filepath: path to the catalog CSV file
    """
    catalog_dir = _BONNER_BRAINIO_HOME / catalog_name
    catalog_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(filepath, catalog_dir / "catalog.csv")


def _lookup(
    *, catalog_name: str, identifier: str, lookup_type: str, class_: str
) -> pd.DataFrame:
    """Look up a file in the catalog.

    :param catalog_name: name of the BrainIO catalog
    :param identifier: identifier of the file, as defined in the BrainIO specification
    :param lookup_type: lookup_type of the file, as defined in the BrainIO specification
    :param class_: class of the file, as defined in the BrainIO specification
    :return: row of the catalog corresponding to the file
    """
    catalog = _load(catalog_name)
    filters = {
        "identifier": catalog["identifier"] == identifier,
        "lookup_type": catalog["lookup_type"] == lookup_type,
        "class": catalog["class"] == class_,
    }
    return catalog.loc[
        filters["identifier"] & filters["lookup_type"] & filters["class"], :
    ]


def _create(catalog_name: str) -> None:
    """Create a catalog at $BONNER_BRAINIO_HOME.

    :param catalog_name: name of the BrainIO catalog
    """
    catalog_path = _BONNER_BRAINIO_HOME / catalog_name / "catalog.csv"
    if catalog_path.exists():
        return
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
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog.to_csv(catalog_path, index=False)


def _load(catalog_name: str) -> pd.DataFrame:
    """Load a catalog.

    :param catalog_name: name of the BrainIO catalog
    :return: catalog as a DataFrame
    """
    path_catalog = _BONNER_BRAINIO_HOME / catalog_name / "catalog.csv"
    if not path_catalog.exists():
        _create(catalog_name)
    return pd.read_csv(path_catalog)


def _append(catalog_name: str, *, entry: Mapping[str, str]) -> pd.DataFrame:
    """Append an entry to the catalog.

    :param catalog_name: name of the BrainIO catalog
    :param entry: a Mapping from column names to values for the entry
    :return: updated catalog with appended row
    """
    catalog = _load(catalog_name)
    catalog = pd.concat([catalog, pd.DataFrame(entry, index=[len(catalog)])])
    catalog.to_csv(_BONNER_BRAINIO_HOME / catalog_name / "catalog.csv", index=False)
    return catalog
