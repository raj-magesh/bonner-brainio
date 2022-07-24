"""TODO add docstring."""

__all__: list[str] = ["Catalog"]

import shutil
import zipfile
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

import netCDF4
import pandas as pd

from ._network import get_network_handler
from ._utils import HOME, compute_sha1
from ._validation import validate_catalog, validate_data_assembly, validate_stimulus_set


class Catalog:
    def __init__(self, identifier: str, *, path: Path | None = None) -> None:
        self.identifier = identifier
        self._path = HOME / self.identifier / "catalog.csv"
        self._create(path=path)
        validate_catalog(path=self._path)

    def _create(self, *, path: Path | None = None) -> None:
        if self._path.exists():
            raise ValueError(
                f"catalog {self.identifier} already exists at f{self._path}"
            )
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if path is None:
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
            validate_catalog(path)
            shutil.copy(path, self._path)

    def _lookup(
        self,
        *,
        identifier: str,
        lookup_type: str,
    ) -> pd.DataFrame | None:
        catalog = pd.read_csv(self._path)
        filter = (catalog["identifier"] == identifier) & (
            catalog["lookup_type"] == lookup_type
        )
        result = catalog.loc[filter, :]

        if len(result) != 0:
            if lookup_type == "assembly":
                assert len(result) == 1, (
                    "The Catalog MUST contain exactly one row corresponding to the Data"
                    f" Assembly {identifier}"
                )
            elif lookup_type == "assembly":
                assert len(result) == 2, (
                    "The Catalog MUST contain exactly two rows corresponding to the"
                    f" Stimulus Set {identifier}"
                )
        return result

    def _append(self, entry: Mapping[str, str]) -> None:
        catalog = pd.read_csv(self._path)
        catalog = pd.concat([catalog, pd.DataFrame(entry, index=[len(catalog)])])
        catalog.to_csv(self._path, index=False)

    def _fetch(self, *, location_type: str, location: str) -> Path:
        path = self._path.parent / Path(urlparse(location).path).name
        if not path.exists():
            handler = get_network_handler(location_type=location_type)
            handler.download(
                location=location,
                filepath=path,
            )
        return path

    def _send(
        self,
        *,
        path: Path,
        identifier: str,
        lookup_type: str,
        class_: str,
        location_type: str,
        location: str,
        stimulus_set_identifier: str = "",
    ) -> None:
        assert not self._lookup(
            identifier=identifier, lookup_type=lookup_type
        ).empty, f"{lookup_type} {identifier} already exists in catalog"
        sha1 = compute_sha1(path)
        handler = get_network_handler(location_type=location_type)
        handler.upload(
            location=location,
            filepath=path,
        )
        self._append(
            {
                "identifier": identifier,
                "lookup_type": lookup_type,
                "class": class_,
                "location_type": location_type,
                "location": location,
                "sha1": sha1,
                "stimulus_set_identifier": stimulus_set_identifier,
            }
        )

    def load_stimulus_set(
        self,
        *,
        identifier: str,
        check_integrity: bool = True,
        validate: bool = True,
    ) -> dict[str, Path]:
        metadata = self._lookup(identifier=identifier, lookup_type="stimulus_set")
        assert not metadata.empty, f"Stimulus Set {identifier} not found in Catalog"

        paths = {}
        for row in metadata.itertuples():
            path = self._fetch(location_type=row.location_type, location=row.location)

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
        check_integrity: bool = True,
        validate: bool = True,
    ) -> Path:
        metadata = self._lookup(identifier=identifier, lookup_type="assembly").to_dict()
        assert not metadata.empty, f"Stimulus Set {identifier} not found in Catalog"

        path = self._fetch(
            location_type=metadata["location_type"], location=metadata["location"]
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
        path_csv: Path,
        path_zip: Path,
        identifier: str,
        location_type: str,
        location_csv: str,
        location_zip: str,
        class_csv: str,
        class_zip: str,
    ) -> None:
        validate_stimulus_set(path_csv=path_csv, path_zip=path_zip)

        self._send(
            path=path_csv,
            identifier=identifier,
            lookup_type="stimulus_set",
            class_=class_csv,
            location_type=location_type,
            location=location_csv,
        )
        self._send(
            path=path_zip,
            identifier=identifier,
            lookup_type="stimulus_set",
            class_=class_zip,
            location_type=location_type,
            location=location_zip,
        )

    def package_data_assembly(
        self,
        *,
        path: Path,
        location_type: str,
        location: str,
        class_: str,
    ) -> None:
        validate_data_assembly(path=path)
        assembly = netCDF4.Dataset(path, "r", format="NETCDF4")
        self._send(
            path=path,
            identifier=assembly.ncattrs()["identifier"],
            lookup_type="assembly",
            class_=class_,
            location_type=location_type,
            location=location,
            stimulus_set_identifier=assembly.ncattrs()["stimulus_set_identifier"],
        )
