"""TODO add docstring."""

__all__: list[str] = []

import os
import zipfile
from pathlib import Path

import netCDF4
import pandas as pd

from ._network import fetch, send
from ._utils import (
    compute_sha1,
    validate_catalog,
    validate_data_assembly,
    validate_stimulus_set,
)

BONNER_BRAINIO_CACHE = Path(
    os.getenv("BONNER_BRAINIO_CACHE", str(Path.home() / ".cache" / "bonner-brainio"))
)


class Catalog:
    def __init__(
        self,
        identifier: str,
        *,
        csv_file: Path | None = None,
        cache_directory: Path | None = None,
    ) -> None:
        """Initialize a Catalog.

        :param identifier: identifier of the Catalog
        :param csv_file: path to the (potentially existing) Catalog CSV file
        :param cache_directory: directory to use as a local file cache
        """
        self.identifier = identifier
        """Identifier of the Catalog."""

        self.csv_file: Path
        """Path to the Catalog CSV file, defaults to $BONNER_BRAINIO_CACHE/<identifier>/catalog.csv."""

        self.cache_directory: Path
        """Local cache directory for files fetched from the Catalog, defaults to $BONNER_BRAINIO_CACHE/<identifier>."""

        if csv_file:
            self.csv_file = csv_file
        else:
            self.csv_file = BONNER_BRAINIO_CACHE / self.identifier / "catalog.csv"

        if not self.csv_file.exists():
            self._create(path=self.csv_file)

        if cache_directory:
            self.cache_directory = cache_directory
        else:
            self.cache_directory = BONNER_BRAINIO_CACHE / self.identifier

        if not self.cache_directory.exists():
            self.cache_directory.mkdir(parents=True, exist_ok=True)

        validate_catalog(path=self.csv_file)

    def load_stimulus_set(
        self,
        *,
        identifier: str,
        use_cached: bool = True,
        check_integrity: bool = True,
        validate: bool = True,
    ) -> dict[str, Path]:
        """Load a Stimulus Set from the Catalog.

        :param identifier: identifier of the Stimulus Set
        :param use_cached: whether to use the local cache, defaults to True
        :param check_integrity: whether to check the SHA1 hashes of the files, defaults to True
        :param validate: whether to ensure that the Stimulus Set conforms to the BrainIO specification, defaults to True
        :return: paths to the Stimulus Set CSV file and ZIP archive, with keys "csv" and "zip" respectively
        """
        metadata = self._lookup(identifier=identifier, lookup_type="stimulus_set")
        assert not metadata.empty, f"Stimulus Set {identifier} not found in Catalog"

        paths = {}
        for row in metadata.itertuples():
            path = fetch(
                path_cache=self.cache_directory,
                location_type=row.location_type,
                location=row.location,
                use_cached=use_cached,
            )

            if check_integrity:
                assert row.sha1 == compute_sha1(
                    path
                ), f"SHA1 hash from the Catalog does not match that of {path}"

            if zipfile.is_zipfile(path):
                paths["zip"] = path
            else:
                paths["csv"] = path

        if validate:
            validate_stimulus_set(path_csv=paths["csv"], path_zip=paths["zip"])

        return paths

    def load_data_assembly(
        self,
        *,
        identifier: str,
        use_cached: bool = True,
        check_integrity: bool = True,
        validate: bool = True,
    ) -> Path:
        """Load a Data Assembly from the Catalog.

        :param identifier: identifier of the Data Assembly
        :param use_cached: whether to use the local cache, defaults to True
        :param check_integrity: whether to check the SHA1 hashes of the files, defaults to True
        :param validate: whether to ensure that the Data Assembly conforms to the BrainIO specification, defaults to True
        :return: path to the Data Assembly netCDF-4 file
        """
        metadata = self._lookup(identifier=identifier, lookup_type="assembly").to_dict()
        assert not metadata.empty, f"Stimulus Set {identifier} not found in Catalog"

        path = fetch(
            path_cache=self.cache_directory,
            location_type=metadata["location_type"],
            location=metadata["location"],
            use_cached=use_cached,
        )

        if check_integrity:
            assert metadata["sha1"] == compute_sha1(
                path
            ), f"SHA1 hash from the Catalog does not match that of {path}"

        if validate:
            validate_data_assembly(path=path)

        return path

    def package_stimulus_set(
        self,
        *,
        identifier: str,
        path_csv: Path,
        path_zip: Path,
        location_type: str,
        location_csv: str,
        location_zip: str,
        class_csv: str,
        class_zip: str,
    ) -> None:
        """Add a Stimulus Set to the Catalog.

        :param identifier: identifier of the Stimulus Set
        :param path_csv: path to the Stimulus Set CSV file
        :param path_zip: path to the Stimulus Set ZIP file
        :param location_type: location_type of the Stimulus Set
        :param location_csv: remote URL of the Stimulus Set CSV file
        :param location_zip: remote URL of the Stimulus Set ZIP archive
        :param class_csv: class of the Stimulus Set CSV file
        :param class_zip: class of the Stimulus Set ZIP archive
        """
        metadata = self._lookup(identifier=identifier, lookup_type="stimulus_set")
        assert metadata.empty, f"Stimulus Set {identifier} already exists in Catalog"

        validate_stimulus_set(path_csv=path_csv, path_zip=path_zip)

        for path, location, class_ in {
            (path_csv, location_csv, class_csv),
            (path_zip, location_zip, class_zip),
        }:
            send(path=path, location_type=location_type, location=location)
            self._append(
                {
                    "identifier": identifier,
                    "lookup_type": "stimulus_set",
                    "class": class_,
                    "location_type": location_type,
                    "location": location,
                    "sha1": compute_sha1(path),
                    "stimulus_set_identifier": "",
                }
            )
        validate_catalog(self.csv_file)

    def package_data_assembly(
        self,
        *,
        path: Path,
        location_type: str,
        location: str,
        class_: str,
    ) -> None:
        """Add a Data Assembly to the Catalog.

        :param path: path to the Data Assembly netCDF-4 file
        :param location_type: location_type of the Data Assembly
        :param location: remote URL of the Data Assembly
        :param class_: class of the Data Assembly
        """
        validate_data_assembly(path=path)

        assembly = netCDF4.Dataset(path, "r", format="NETCDF4")
        identifier = assembly.__dict__["identifier"]

        metadata = self._lookup(identifier=identifier, lookup_type="assembly")
        assert metadata.empty, f"Data Assembly {identifier} already exists in Catalog"

        send(path=path, location_type=location_type, location=location)
        self._append(
            {
                "identifier": identifier,
                "lookup_type": "assembly",
                "class": class_,
                "location_type": location_type,
                "location": location,
                "sha1": compute_sha1(path),
                "stimulus_set_identifier": assembly.__dict__["stimulus_set_identifier"],
            }
        )
        validate_catalog(self.csv_file)

    def _create(self, path: Path) -> None:
        """Create a new Catalog CSV file.

        :param path: path where the Catalog CSV file should be created
        """
        path.parent.mkdir(parents=True, exist_ok=True)
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
        catalog.to_csv(path, index=False)

    def _lookup(
        self,
        *,
        identifier: str,
        lookup_type: str,
    ) -> pd.DataFrame:
        """Look up the metadata for a Data Assembly or Stimulus Set in the Catalog.

        :param identifier: identifier of the Data Assembly or Stimulus Set
        :param lookup_type: 'assembly' or 'stimulus_set', when looking up Data Assemblies or Stimulus Sets respectively
        :return: metadata corresponding to the Data Assembly or Stimulus Set
        """
        catalog = pd.read_csv(self.csv_file)
        filter = (catalog["identifier"] == identifier) & (
            catalog["lookup_type"] == lookup_type
        )
        return catalog.loc[filter, :]

    def _append(self, entry: dict[str, str]) -> None:
        """Append an entry to the Catalog.

        :param entry: a row to be appended to the Catalog CSV file, where keys correspond to column header names
        """
        catalog = pd.read_csv(self.csv_file)
        catalog = pd.concat([catalog, pd.DataFrame(entry, index=[len(catalog)])])
        catalog.to_csv(self.csv_file, index=False)
