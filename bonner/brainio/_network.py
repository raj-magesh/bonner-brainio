"""TODO add docstring."""

__all__: list[str] = []

import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

import boto3
import botocore
from botocore.config import Config


class NetworkHandler(ABC):
    """An abstract base class that implements the 'upload' and 'download' methods."""

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def upload(self, *, local_path: Path, remote_url: str) -> None:
        """Upload a file to the remote.

        :param local_path: local path of the file
        :param remote_url: remote URL of the file
        """
        raise NotImplementedError()

    @abstractmethod
    def download(self, *, local_path: Path, remote_url: str) -> None:
        """Download a file from the remote.

        :param local_path: local path of the file
        :param remote_url: remote URL of the file
        """
        raise NotImplementedError()


class RsyncHandler(NetworkHandler):
    """Uses Rsync to upload and download files to/from a networked server."""

    def upload(self, local_path: Path, remote_url: str) -> None:
        """Upload a file to the remote using Rsync.

        :param local_path: local path of the file
        :param remote_url: remote URL of the file (<server-name>:<remote-path>)
        """
        subprocess.run(
            [
                "ssh",
                urlparse(remote_url).scheme,
                "mkdir",
                "-p",
                str(Path(urlparse(remote_url).path).parent),
            ],
            check=True,
        )
        subprocess.run(
            [
                "rsync",
                "-vzhW",
                "--progress",
                str(local_path),
                remote_url,
            ],
            check=True,
        )

    def download(self, local_path: Path, remote_url: str) -> None:
        """Download a file from the remote using Rsync.

        :param local_path: local path of the file
        :param remote_url: remote URL of the file (<server-name>:<remote-path>)
        """
        if not local_path.exists():
            subprocess.run(
                ["rsync", "-vzhW", "--progress", remote_url, str(local_path)],
                check=True,
            )


class S3Handler(NetworkHandler):
    """Upload and download files to/from Amazon S3."""

    def upload(self, local_path: Path, remote_url: str) -> None:
        """Upload a file to an S3 bucket.

        :param local_path: local path of the file
        :param remote_url: remote URL of the file
        """
        client = boto3.client("s3")
        client.upload_file(str(local_path), remote_url)

    def download(self, local_path: Path, remote_url: str) -> None:
        """Download a file from an S3 bucket.

        :param local_path: local path of the file
        :param remote_url: remote URL of the file
        """
        parsed_url = urlparse(remote_url)
        split_path = parsed_url.path.lstrip("/").split("/")

        if parsed_url.hostname:
            if "s3." in parsed_url.hostname:
                bucket_name = parsed_url.hostname.split(".s3.")[0]
                relative_path = os.path.join(*(split_path))
            elif "s3-" in parsed_url.hostname:
                bucket_name = split_path[0]
                relative_path = os.path.join(*(split_path[1:]))
        else:
            raise ValueError(f"parsing the URL {remote_url} did not yield any hostname")

        try:
            self.download_helper(
                local_path=local_path,
                bucket_name=bucket_name,
                relative_path=relative_path,
                config=None,
            )
        except Exception:
            config = Config(signature_version=botocore.UNSIGNED)
            self.download_helper(
                local_path=local_path,
                bucket_name=bucket_name,
                relative_path=relative_path,
                config=config,
            )

    def download_helper(
        self,
        *,
        local_path: Path,
        bucket_name: str,
        relative_path: str,
        config: Config | None,
    ) -> None:
        """Utility function for downloading a file from S3.

        :param local_path: local path to file
        :param bucket_name: name of the S3 bucket
        :param relative_path: relative path of the file within the S3 bucket
        :param config: TODO config for Amazon S3
        """
        s3 = boto3.resource("s3", config=config)
        obj = s3.Object(bucket_name, relative_path)
        obj.download_file(local_path)


def get_network_handler(location_type: str) -> NetworkHandler:
    """Get the correct network handler for the provided location_type.

    :param location_type: location_type, as defined in the BrainIO specification
    :raises ValueError: if the location_type provided is unsupported
    :return: the network handler used to upload/download files
    """
    if location_type == "rsync":
        return RsyncHandler()
    elif location_type == "S3":
        return S3Handler()
    else:
        raise ValueError(f"location_type {location_type} is unsupported")


def fetch(
    *, path_cache: Path, location_type: str, location: str, use_cached: bool = True
) -> Path:
    """Fetch a file from <location> to the local cache directory.

    :param cache: path to the local cache directory
    :param location_type: method to use to fetch files from the location (e.g. "rsync", "s3")
    :param location: remote URL of the file
    :param use_cached: whether to use the local cache
    :return: local path to the fetched file
    """
    path = path_cache / Path(urlparse(location).path).name
    if (not path.exists()) or (not use_cached):
        handler = get_network_handler(location_type)
        handler.download(
            remote_url=location,
            local_path=path,
        )
    return path


def send(
    *,
    path: Path,
    location_type: str,
    location: str,
) -> None:
    """Send a file to <location>.

    :param path: local path to the file
    :param location_type: method to use to fetch files from the location (e.g. "rsync", "s3")
    :param location: remote URL of the file
    """
    handler = get_network_handler(location_type=location_type)
    handler.upload(
        remote_url=location,
        local_path=path,
    )
