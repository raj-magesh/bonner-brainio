import pandas as pd
import xarray as xr

from .core import BRAINIO_HOME, fetch, package_assembly


def load(
    *,
    catalog_name: str,
    identifier: str,
    check_integrity: bool = True,
) -> xr.DataArray:
    """Load a BrainIO assembly from a catalog as a DataArray.

    :param catalog_name: name of the BrainIO catalog
    :type catalog_name: str
    :param identifier: identifier of the assembly, as defined in the BrainIO specification
    :type identifier: str
    :param check_integrity: whether to check the SHA1 hash of the file, defaults to True
    :type check_integrity: bool, optional
    :return: the BrainIO assembly
    :rtype: xr.DataArray
    """
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
    """Package a DataArray as a BrainIO assembly.

    :param assembly: the DataArray
    :type assembly: xr.DataArray
    :param catalog_name: name of the BrainIO catalog
    :type catalog_name: str
    :param location_type: location_type of the assembly, as defined in the BrainIO specification
    :type location_type: str
    :param location: location of the assembly, as defined in the BrainIO specification
    :type location: str
    """
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


def merge(assembly: xr.DataArray, stimulus_set: pd.DataFrame) -> xr.DataArray:
    """Merge the metadata columns from a stimulus set into an assembly.

    :param assembly: the BrainIO assembly
    :type assembly: xr.DataArray
    :param stimulus_set: the BrainIO stimulus set
    :type stimulus_set: pd.DataFrame
    :return: the updated BrainIO assembly
    :rtype: xr.DataArray
    """
    assembly = assembly.load()
    stimulus_set = stimulus_set.loc[
        stimulus_set["stimulus_id"].isin(assembly["stimulus_id"].values), :
    ]
    for column in stimulus_set.columns:
        if column == "stimulus_id" or column == "filename":
            continue
        assembly[column] = ("presentation", stimulus_set[column])
    return assembly
