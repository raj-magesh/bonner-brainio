"""TODO add docstring."""

__all__: list[str] = ["package", "load"]

from pathlib import Path

import netCDF4

from ._network import fetch, send


def package(
    *,
    filepath: Path,
    catalog_name: str,
    class_: str,
    location_type: str,
    location: str,
) -> None:
    """Package an assembly.

    :param filepath: path to a netCDF-4 file corresponding to a :ref:`BrainIO assembly <spec_assembly>`
    :param catalog_name: name of the :ref:`BrainIO catalog <spec_catalog>`
    :param class_: class of the :ref:`BrainIO assembly <spec_assembly>`
    :param location_type: location_type of the :ref:`BrainIO assembly <spec_assembly>`
    :param location: location of the :ref:`BrainIO assembly <spec_assembly>`
    """

    _validate(filepath)
    file = netCDF4.Dataset(filepath, mode="r", format="NETCDF4")

    send(
        identifier=file.__dict__["identifier"],
        lookup_type="assembly",
        class_=class_,
        filepath=filepath,
        catalog_name=catalog_name,
        location_type=location_type,
        location=location,
        stimulus_set_identifier=file.__dict__["stimulus_set_identifier"],
    )


def load(
    *,
    catalog_identifier: str,
    identifier: str,
    check_integrity: bool,
) -> Path:
    """Load an assembly from a catalog.

    :param catalog_identifier: name of the BrainIO catalog
    :param identifier: identifier of the BrainIO assembly
    :param check_integrity: _description_
    :return: _description_
    """
    return fetch(
        catalog_name=catalog_identifier,
        identifier=identifier,
        lookup_type="assembly",
        check_integrity=check_integrity,
    )


def _validate(filepath: Path) -> None:
    """Validate an assembly and ensure that it follows the BrainIO specification.

    :param filepath: path to a netCDF-4 file corresponding to a :ref:`BrainIO assembly <spec_assembly>`
    """

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
