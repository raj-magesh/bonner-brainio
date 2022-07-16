# Bonner Lab BrainIO

This is an implementation of the [BrainIO specification](https://github.com/brain-score/brainio/blob/main/docs/SPECIFICATION.md).

## Installation

`pip install git+https://github.com/raj-magesh/bonner-brainio`

## API

### bonner.brainio.core

`core` is a complete implementation of the [BrainIO specification](https://github.com/brain-score/brainio/blob/main/docs/SPECIFICATION.md) that exposes the following public functions:

- `BRAINIO_HOME`: `pathlib.Path` to directory where all BrainIO files are stored
- `import_catalog`: imports an existing catalog from a file
- `fetch`: fetches an item from a catalog
- `package_assembly`: packages an assembly given its netCDF4 file
- `package_stimulus_set`: packages a stimulus set given its .csv and .zip files

### bonner.brainio.assembly

`assembly.py` provides convenience functions for loading and packaging assemblies in `xarray` format:

- `load`: loads an assembly into an `xarray.DataArray`
- `package`: packages an assembly given an `xarray.DataArray`
- `merge`: adds the metadata from a stimulus set to an assembly

### bonner.brainio.stimulus_set

`stimulus_set.py` provides convenience functions for packaging and loading stimulus sets:

- `load`: returns a stimulus set's metadata as a `pandas.DataFrame`, extracts the ZIP archive, and also returns the path to the stimuli
- `package`: packages a stimulus set given the metadata as a `pandas.DataFrame` and the path to the stimuli

## Environment variables

All BrainIO data will be stored at the path specified by `BRAINIO_HOME`.

## Dependencies

- `boto3`: required for the S3 backend
- `pandas`: handling the catalog (`catalog.csv`) and the stimulus set metadata .csv files
- `netCDF4`: validating assemblies
- `xarray`: using the convenience functions in `assembly.py`

## File organization

- Catalogs are stored at `$BRAINIO_HOME/<catalog-name>/catalog.csv`
- When loading assemblies and stimulus sets, the files are downloaded to `$BRAINIO_HOME/<catalog-name>/`
- When packaging assemblies and stimulus sets using the convenience functions, the files are first placed in `$BRAINIO_HOME/<catalog-name>/` before being pushed to the specified remote location

## Things to do

- TODO implement logging
- TODO write tests
- TODO improve the specification to conform to the original BrainIO team's implementation
- TODO remove `setup.py` once `setuptools` [allows editable installs with a `pyproject.toml`](https://github.com/pypa/setuptools/issues/2816)
