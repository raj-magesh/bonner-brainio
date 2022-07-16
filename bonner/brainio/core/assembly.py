from pathlib import Path

import netCDF4

from .utils import _package


def package(
    *,
    filepath: Path,
    class_: str,
    catalog_name: str,
    location_type: str,
    location: str,
) -> None:

    _validate(filepath)
    file = netCDF4.Dataset(filepath, mode="r", format="NETCDF4")

    _package(
        identifier=file.__dict__["identifier"],
        lookup_type="assembly",
        class_=class_,
        filepath=filepath,
        catalog_name=catalog_name,
        location_type=location_type,
        location=location,
        stimulus_set_identifier=file.__dict__["stimulus_set_identifier"],
    )


def _validate(filepath: Path):
    assembly = netCDF4.Dataset(filepath, "r", format="NETCDF4")
    assert (
        "presentation" in assembly.dimensions
    ), "'presentation' must be a dimension in the dataset"
    assert (
        "stimulus_id" in assembly.variables
    ), "'stimulus_id' must be a variable in the dataset"
    assert (
        "presentation" in assembly.variables["stimulus_id"].dimensions
    ), "'stimulus_id' must be a coordinate along the dimension 'presentation'"

    assert (
        "identifier" in assembly.ncattrs()
    ), "'identifier' must be a global attribte in the dataset"
    assert (
        "stimulus_set_identifier" in assembly.ncattrs()
    ), "'stimulus_set_identifier' must be a global attribte in the dataset"
