from types import SimpleNamespace

import pytest
from django.http import Http404

from apps.core.downloads import internal_file_download


def test_private_download_rejects_path_traversal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "uploads"

    file_field = SimpleNamespace(
        name="evidence/../private.pdf",
        path=str(tmp_path / "private.pdf"),
    )

    with pytest.raises(Http404, match="Invalid file path"):
        internal_file_download(file_field)


def test_private_download_rejects_files_outside_media_root(settings, tmp_path):
    media_root = tmp_path / "uploads"
    media_root.mkdir()
    outside_file = tmp_path / "private.pdf"
    outside_file.write_bytes(b"private")
    settings.MEDIA_ROOT = media_root

    file_field = SimpleNamespace(
        name="evidence/private.pdf",
        path=str(outside_file),
    )

    with pytest.raises(Http404, match="outside the private media directory"):
        internal_file_download(file_field)
