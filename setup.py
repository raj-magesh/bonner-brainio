from setuptools import setup, find_namespace_packages

requirements = (
    "boto3",
    "pandas",
    "xarray",
    "netCDF4",
)

setup(
    name="bonner-brainio",
    version="0.1.0",
    packages=find_namespace_packages(),
    install_requires=requirements,
)
