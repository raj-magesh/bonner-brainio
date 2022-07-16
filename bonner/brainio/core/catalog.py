from typing import Mapping
from pathlib import Path
import shutil

import pandas as pd

from .utils import BRAINIO_HOME


def _import(
    *,
    catalog_name: str,
    filepath: Path,
) -> pd.DataFrame:
    catalog_dir = BRAINIO_HOME / catalog_name
    catalog_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(filepath, catalog_dir / "catalog.csv")


def _lookup(
    *, catalog_name: str, identifier: str, lookup_type: str, class_: str
) -> pd.DataFrame:
    catalog = _load(catalog_name)
    filters = {
        "identifier": catalog["identifier"] == identifier,
        "lookup_type": catalog["lookup_type"] == lookup_type,
        "class": catalog["class"] == class_,
    }
    return catalog.loc[
        filters["identifier"] & filters["lookup_type"] & filters["class"], :
    ]


def _initialize(catalog_name: str) -> None:
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


def _load(catalog_name: str) -> pd.DataFrame:
    path_catalog = BRAINIO_HOME / catalog_name / "catalog.csv"
    if not path_catalog.exists():
        _initialize(catalog_name)
    return pd.read_csv(path_catalog)


def _append(catalog_name: str, *, entry: Mapping[str, str]) -> pd.DataFrame:
    catalog = _load(catalog_name)
    catalog = pd.concat([catalog, pd.DataFrame(entry, index=[len(catalog)])])
    catalog.to_csv(BRAINIO_HOME / catalog_name / "catalog.csv", index=False)
    return catalog
