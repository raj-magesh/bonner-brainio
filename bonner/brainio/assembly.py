from typing import Optional

import xarray as xr

from .core import BRAINIO_HOME, lookup, fetch, send
from .stimulus_set import load as load_stimulus_set


def package(
    *,
    identifier: str,
    assembly: xr.DataArray,
    catalog_name: str,
    location_type: str,
    location: str,
) -> None:

    assert lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type="assembly",
        class_="netcdf4"
    ).empty, f"assembly {identifier} already exists in catalog {catalog_name}"

    _verify(
        identifier=identifier,
        assembly=assembly,
    )

    filepath = BRAINIO_HOME / catalog_name / f"{identifier}.nc"
    assembly.to_netcdf(filepath)

    send(
        identifier=identifier,
        lookup_type="assembly",
        class_="netcdf4",
        filepath=filepath,
        catalog_name=catalog_name,
        location_type=location_type,
        url=f"{location}/{filepath.name}",
        stimulus_set_identifier=assembly.attrs["stimulus_set_identifier"],
    )


def load(
    *,
    catalog_name: str,
    identifier: str,
    check_integrity: bool = True,
    merge_metadata: bool = True,
) -> xr.DataArray:
    filepath = fetch(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type="assembly",
        class_="netcdf4",
        check_integrity=check_integrity,
    )
    metadata = lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type="assembly",
        class_="netcdf4",
    )
    assembly = xr.open_dataarray(filepath)

    _verify(
        identifier=identifier,
        assembly=assembly,
        stimulus_set_identifier=metadata["stimulus_set_identifier"].item()
    )

    if merge_metadata:
        assembly = assembly.load()
        stimulus_set, _ = load_stimulus_set(
            catalog_name=catalog_name,
            identifier=metadata["stimulus_set_identifier"].item(),
            check_integrity=check_integrity,
        )
        stimulus_set = stimulus_set.loc[
            stimulus_set["stimulus_id"].isin(assembly["stimulus_id"].values), :
        ]
        for column in stimulus_set.columns:
            if column == "stimulus_id" or column == "filename":
                continue
            assembly[column] = ("presentation", stimulus_set[column])
    return assembly


def _verify(
    *,
    identifier: str,
    assembly: xr.DataArray,
    stimulus_set_identifier: Optional[str] = "",
) -> None:
    assert all(
        [
            key in assembly.attrs.keys()
            for key in ("identifier", "stimulus_set_identifier")
        ]
    )
    assert assembly.attrs["identifier"] == identifier
    if stimulus_set_identifier:
        assert assembly.attrs["stimulus_set_identifier"] == stimulus_set_identifier
    assert "presentation" in assembly.dims
    assert "stimulus_id" in assembly["presentation"].coords
