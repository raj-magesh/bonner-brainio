from typing import Optional
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse
import subprocess
import os

import boto3
import botocore
from botocore.config import Config

from .catalog import _lookup, _append
from .utils import BRAINIO_HOME, _compute_sha1


def fetch(
    *,
    catalog_name: str,
    identifier: str,
    lookup_type: str,
    class_: str,
    check_integrity: bool,
) -> Path:
    """Fetch a file from the catalog.

    :param catalog_name: name of the BrainIO catalog
    :type catalog_name: str
    :param identifier: identifier of the file, as defined in the BrainIO specification
    :type identifier: str
    :param lookup_type: lookup_type of the file, as defined in the BrainIO specification
    :type lookup_type: str
    :param class_: class of the file, as defined in the BrainIO specification
    :type class_: str
    :param check_integrity: whether to check the SHA1 hash of the file
    :type check_integrity: bool
    :return: path to the file
    :rtype: Path
    """
    metadata = _lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type=lookup_type,
        class_=class_,
    )
    assert (
        not metadata.empty
    ), f"{lookup_type} {identifier} not found in catalog {catalog_name}"
    filepath = (
        BRAINIO_HOME
        / catalog_name
        / Path(urlparse(metadata["location"].item()).path).name
    )
    if not filepath.exists():
        handler = _get_network_handler(location_type=metadata["location_type"].item())
        handler.download(
            location=metadata["location"].item(),
            filepath=filepath,
        )
    if check_integrity:
        assert metadata["sha1"].item() == _compute_sha1(
            filepath
        ), f"sha1 does not match: {filepath} has been corrupted"
    return filepath


def _package(
    *,
    identifier: str,
    lookup_type: str,
    class_: str,
    filepath: Path,
    catalog_name: str,
    location_type: str,
    location: str,
    stimulus_set_identifier: str = "",
) -> None:
    """Package a file to the catalog.

    :param identifier: identifier of the file, as defined in the BrainIO specification
    :type identifier: str
    :param lookup_type: lookup_type of the file, as defined in the BrainIO specification
    :type lookup_type: str
    :param class_: class of the file, as defined in the BrainIO specification
    :type class_: str
    :param filepath: path to the file
    :type filepath: Path
    :param catalog_name: name of the BrainIO catalog
    :type catalog_name: str
    :param location_type: location_type of the file, as defined in the BrainIO specification
    :type location_type: str
    :param location: location of the file, as defined in the BrainIO specification
    :type location: str
    :param stimulus_set_identifier: identifier of the stimulus set associated with the file, if it is an assembly, defaults to ""
    :type stimulus_set_identifier: str, optional
    """
    assert _lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type=lookup_type,
        class_=class_,
    ).empty, f"{lookup_type} {identifier} already exists in catalog {catalog_name}"

    sha1 = _compute_sha1(filepath)
    handler = _get_network_handler(location_type=location_type)
    handler.upload(
        location=location,
        filepath=filepath,
    )

    _append(
        catalog_name,
        entry={
            "identifier": identifier,
            "lookup_type": lookup_type,
            "class": class_,
            "location_type": location_type,
            "location": location,
            "sha1": sha1,
            "stimulus_set_identifier": stimulus_set_identifier,
        },
    )


class _NetworkHandler(ABC):
    """An abstract base class that implements the 'upload' and 'download' methods."""

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def upload(self, *, filepath: Path, location: str) -> None:
        """Upload a file to the remote.

        :param filepath: local path of the file
        :type filepath: Path
        :param location: remote path of the file
        :type location: str
        """
        raise NotImplementedError()

    @abstractmethod
    def download(self, *, filepath: Path, location: str) -> None:
        """Download a file from the remote.

        :param filepath: local path of the file
        :type filepath: Path
        :param location: remote path of the file
        :type location: str
        """
        raise NotImplementedError()


class _RsyncHandler(_NetworkHandler):
    """Uses Rsync to upload and download files to/from a networked server."""

    def upload(self, filepath: Path, location: str) -> None:
        """Upload a file to the remote using Rsync.

        :param filepath: local path of the file
        :type filepath: Path
        :param location: remote path of the file (<server-name>:<remote-path>)
        :type location: str
        """
        subprocess.run(
            [
                "ssh",
                urlparse(location).scheme,
                "mkdir",
                "-p",
                str(Path(urlparse(location).path).parent),
            ],
            check=True,
        )
        subprocess.run(
            [
                "rsync",
                "-vzhW",
                "--recursive",
                "--relative",
                "--progress",
                str(filepath),
                location,
            ],
            check=True,
        )

    def download(self, filepath: Path, location: str) -> None:
        """Download a file from the remote using Rsync.

        :param filepath: local path of the file
        :type filepath: Path
        :param location: remote path of the file (<server-name>:<remote-path>)
        :type location: str
        """
        if not filepath.exists():
            subprocess.run(
                ["rsync", "-vzhW", "--progress", location, str(filepath)],
                check=True,
            )


class _S3Handler(_NetworkHandler):
    """Upload and download files to/from Amazon S3."""

    def upload(self, filepath: Path, location: str) -> None:
        """Upload a file to an S3 bucket.

        :param filepath: local path of the file
        :type filepath: Path
        :param location: remote URL of the file
        :type location: str
        """
        client = boto3.client("s3")
        client.upload_file(str(filepath), location)

    def download(self, filepath: Path, location: str) -> None:
        """Download a file from an S3 bucket.

        :param filepath: local path of the file
        :type filepath: Path
        :param location: remote URL of the file
        :type location: str
        """
        parsed_url = urlparse(location)
        split_path = parsed_url.path.lstrip("/").split("/")

        if parsed_url.hostname:
            if "s3." in parsed_url.hostname:
                bucket_name = parsed_url.hostname.split(".s3.")[0]
                relative_path = os.path.join(*(split_path))
            elif "s3-" in parsed_url.hostname:
                bucket_name = split_path[0]
                relative_path = os.path.join(*(split_path[1:]))
        else:
            raise ValueError(f"parsing the URL {location} did not yield any hostname")

        try:
            self._download_helper(
                filepath=filepath,
                bucket_name=bucket_name,
                relative_path=relative_path,
                config=None,
            )
        except:
            config = Config(signature_version=botocore.UNSIGNED)
            self._download_helper(
                filepath=filepath,
                bucket_name=bucket_name,
                relative_path=relative_path,
                config=config,
            )

    def _download_helper(
        self,
        *,
        filepath: Path,
        bucket_name: str,
        relative_path: str,
        config: Optional[Config],
    ) -> None:
        """Utility function for downloading a file from S3.

        :param filepath: local path to file
        :type filepath: Path
        :param bucket_name: name of the S3 bucket
        :type bucket_name: str
        :param relative_path: relative path of the file within the S3 bucket
        :type relative_path: str
        :param config: TODO config for Amazon S3
        :type config: Optional[Config]
        """
        s3 = boto3.resource("s3", config=config)
        obj = s3.Object(bucket_name, relative_path)
        obj.download_file(filepath)


def _get_network_handler(location_type: str) -> _NetworkHandler:
    """Get the correct network handler for the provided location_type.

    :param location_type: location_type, as defined in the BrainIO specification
    :type location_type: str
    :raises ValueError: if the location_type provided is unsupported
    :return: the network handler used to upload/download files
    :rtype: _NetworkHandler
    """
    if location_type == "rsync":
        return _RsyncHandler()
    elif location_type == "S3":
        return _S3Handler()
    else:
        raise ValueError(f"location_type {location_type} is unsupported")
