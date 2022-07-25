# Bonner Lab BrainIO

This is an implementation of the [BrainIO specification](https://github.com/brain-score/brainio/blob/main/docs/SPECIFICATION.md).

## Installation

`pip install git+https://github.com/BonnerLab/bonner-brainio`

## Environment variables

All Bonner-BrainIO data will be stored at the path specified by `BONNER_BRAINIO_CACHE`.

## Dependencies

- `boto3`: required for the S3 backend
- `pandas`: handling the catalog (`catalog.csv`) and the stimulus set metadata .csv files
- `netCDF4`: validating assemblies

## File organization

- Catalogs are stored at `$BONNER_BRAINIO_CACHE/<catalog-identifier>/catalog.csv`
- When loading assemblies and stimulus sets, the files are downloaded to `$BONNER_BRAINIO_CACHE/<catalog-identifier>/`
- When packaging assemblies and stimulus sets using the convenience functions, the files are first placed in `$BONNER_BRAINIO_CACHE/<catalog-identifier>/` before being pushed to the specified remote location

## Things to do

- TODO setup tox, CI, logging, tests, bandit
- TODO improve the specification to conform to the original BrainIO team's implementation
- TODO remove `setup.py` once `setuptools` [allows editable installs with a `pyproject.toml`](https://github.com/pypa/setuptools/issues/2816)
- TODO several imports are unnecessary and should be wrapped in `if typing.TYPE_CHECKING`, but this breaks Sphinx's autodoc extension
