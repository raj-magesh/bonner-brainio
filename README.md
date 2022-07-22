# Bonner Lab BrainIO

This is an implementation of the [BrainIO specification](https://github.com/brain-score/brainio/blob/main/docs/SPECIFICATION.md).

## Installation

`pip install git+https://github.com/BonnerLab/bonner-brainio`

## API

`bonner.brainio` exposes the following public functions:

- `create_catalog`: creates a new catalog
- `import_catalog`: imports an existing catalog from a file
- `fetch`: fetches an item from a catalog
- `package_stimulus_set`: packages a stimulus set given its .csv and .zip files
- `package_assembly`: packages an assembly given its netCDF4 file

## Environment variables

All Bonner-BrainIO data will be stored at the path specified by `BONNER_BRAINIO_HOME`.

## Dependencies

- `boto3`: required for the S3 backend
- `pandas`: handling the catalog (`catalog.csv`) and the stimulus set metadata .csv files
- `netCDF4`: validating assemblies

## File organization

- Catalogs are stored at `$BONNER_BRAINIO_HOME/<catalog-name>/catalog.csv`
- When loading assemblies and stimulus sets, the files are downloaded to `$BONNER_BRAINIO_HOME/<catalog-name>/`
- When packaging assemblies and stimulus sets using the convenience functions, the files are first placed in `$BONNER_BRAINIO_HOME/<catalog-name>/` before being pushed to the specified remote location

## Things to do

- TODO implement logging
- TODO write tests
- TODO improve the specification to conform to the original BrainIO team's implementation
- TODO remove `setup.py` once `setuptools` [allows editable installs with a `pyproject.toml`](https://github.com/pypa/setuptools/issues/2816)
