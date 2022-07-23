"""TODO add docstring."""

__all__: list[str] = []

import shutil
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from ._utils import HOME


class Catalog:
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self._path = HOME / self.identifier / "catalog.csv"

    def create(self, *, filepath: Path | None = None) -> None:
        """Create a new catalog or import an existing one.

        :param filepath: path to an existing Catalog
        """
        if self._path.exists():
            raise ValueError(f"catalog {self.identifier} already exists at f{HOME}")
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if filepath is not None:
            catalog = pd.DataFrame(
                data=None,
                columns=(
                    "identifier",
                    "lookup_type",
                    "sha1",
                    "location_type",
                    "location",
                    "stimulus_set_identifier",
                    "class",
                ),
            )
            catalog.to_csv(self._path, index=False)
        else:
            shutil.copy(filepath, self._path)

    def _lookup(
        self,
        **kwargs: str | None,
    ) -> pd.DataFrame:
        """Look up an entry in the catalog."""
        catalog = pd.read_csv(self._path)
        filter = pd.DataFrame(
            {key: catalog[key] == value for key, value in kwargs.items() if value}
        ).all(axis="columns")
        return catalog.loc[filter, :]

    def _append(self, *, entry: Mapping[str, str]) -> None:
        """Append an entry to the catalog.

        :param entry: a Mapping from column names to values for the entry
        """
        catalog = pd.read_csv(self._path)
        catalog = pd.concat([catalog, pd.DataFrame(entry, index=[len(catalog)])])
        catalog.to_csv(self._path, index=False)
