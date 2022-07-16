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
from .network import _get_network_handler


def fetch(
    *,
    catalog_name: str,
    identifier: str,
    lookup_type: str,
    class_: str,
    check_integrity: bool,
) -> Path:
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

    assert _lookup(
        catalog_name=catalog_name,
        identifier=identifier,
        lookup_type=lookup_type,
        class_=class_,
    ).empty, f"{lookup_type} {identifier} already exists in catalog {catalog_name}"

    sha1 = _compute_sha1(filepath)
    handler = _get_network_handler(location_type=location_type)
    handler.download(
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


def _get_network_handler(location_type: str) -> None:
    if location_type == "rsync":
        return _RsyncHandler()
    elif location_type == "S3":
        return _S3Handler()
    else:
        raise ValueError(f"location_type {location_type} is unsupported")


class _NetworkHandler(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def upload(self, *, filepath: Path, location: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def download(self, *, filepath: Path, location: str) -> None:
        raise NotImplementedError()


class _RsyncHandler(_NetworkHandler):
    def upload(self, filepath: Path, location: str) -> None:
        subprocess.run(
            [
                "rsync",
                "-vzhW",
                "--progress",
                str(filepath),
                location,
            ],
            check=True,
        )

    def download(self, filepath: Path, location: str) -> None:
        if not filepath.exists():
            subprocess.run(
                ["rsync", "-vzhW", "--progress", location, str(filepath)],
                check=True,
            )


class _S3Handler(_NetworkHandler):
    def upload(self, filepath: Path, location: str) -> None:
        client = boto3.client("s3")
        client.upload_file(str(filepath), location)

    def download(self, filepath: Path, location: str) -> None:
        parsed_url = urlparse(location)
        split_path = parsed_url.path.lstrip("/").split("/")

        if "s3." in parsed_url.hostname:
            bucket_name = parsed_url.hostname.split(".s3.")[0]
            relative_path = os.path.join(*(split_path))
        elif "s3-" in parsed_url.hostname:
            bucket_name = split_path[0]
            relative_path = os.path.join(*(split_path[1:]))

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
        s3 = boto3.resource("s3", config=config)
        obj = s3.Object(bucket_name, relative_path)
        obj.download_file(filepath)
