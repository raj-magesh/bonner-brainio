import pandas as pd
import xarray as xr

from .core import BRAINIO_HOME, fetch, package_assembly


def load(
    *,
    catalog_name: str,
    identifier: str,
    check_integrity: bool = True,
) -> xr.DataArray:
    filepath = fetch(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type="assembly",
        class_="netcdf4",
        check_integrity=check_integrity,
    )
    assembly = xr.open_dataarray(filepath)
    return assembly


def package(
    *,
    assembly: xr.DataArray,
    catalog_name: str,
    location_type: str,
    location: str,
) -> None:

    identifier = assembly.attrs["identifier"]
    filepath = BRAINIO_HOME / catalog_name / f"{identifier}.nc"
    assembly = assembly.to_dataset(name=identifier, promote_attrs=True)
    assembly.to_netcdf(filepath)

    package_assembly(
        filepath=filepath,
        class_="netcdf4",
        catalog_name=catalog_name,
        location_type=location_type,
        location=f"{location}/{filepath.name}",
    )


def merge_stimulus_set_metadata(assembly: xr.DataArray, stimulus_set: pd.DataFrame):
    assembly = assembly.load()
    stimulus_set = stimulus_set.loc[
        stimulus_set["stimulus_id"].isin(assembly["stimulus_id"].values), :
    ]
    for column in stimulus_set.columns:
        if column == "stimulus_id" or column == "filename":
            continue
        assembly[column] = ("presentation", stimulus_set[column])
    return assembly
