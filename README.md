# Bonner Lab BrainIO

This is an implementation of the [BrainIO specification](https://github.com/brain-score/brainio/blob/main/docs/SPECIFICATION.md).

## API

`core.py` is a complete implementation of the [BrainIO specification](https://github.com/brain-score/brainio/blob/main/docs/SPECIFICATION.md) that exposes the following public functions:

- `lookup`: reads metadata about an item from a catalog
- `import_catalog`: imports an existing catalog from a file
- `fetch`: fetches an item from a catalog
- `package_assembly`: packages an assembly given its netCDF4 file
- `package_stimulus_set`: packages a stimulus set given its .csv and .zip files

`assembly.py` provides convenience functions for loading and packaging assemblies in `xarray` format:

- `load`: loads an assembly into an `xarray.DataArray`
- `package`: packages an assembly given an `xarray.DataArray`
- `merge_stimulus_set_metadata`: adds the metadata from a stimulus set to an assembly

`stimulus_set.py` provides convenience functions for packaging and loading stimulus sets:

- `load`: returns a stimulus set's metadata as a `pandas.DataFrame`, extracts the ZIP archive, and also returns the path to the stimuli
- `package`: packages a stimulus set given the metadata as a `pandas.DataFrame` and the path to the stimuli

## Environment variables

All BrainIO data will be stored at the path specified by `BRAINIO_HOME`.

## Dependencies

- `pandas`: handling the catalog (`catalog.csv`) and the stimulus set metadata .csv files
- `netCDF4`: validating assemblies
- `xarray`: using the convenience functions in `assembly.py`

## File organization

- Catalogs are stored at `$BRAINIO_HOME/<catalog-name>/catalog.csv`
- When loading assemblies and stimulus sets, the files are downloaded to `$BRAINIO_HOME/<catalog-name>/`
- When packaging assemblies and stimulus sets using the convenience functions, the files are first placed in `$BRAINIO_HOME/<catalog-name>/` before being pushed to the specified remote location

## Design considerations

- Simplicity: avoid features we in the Bonner Lab won't use
- Conformity: follow the BrainIO specification exactly
- Extensibility: don't create complex data structures beyond those provided by standard libraries
