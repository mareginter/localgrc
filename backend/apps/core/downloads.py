"""Private media downloads served by Nginx after Django authorization."""

import mimetypes
import os
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.http import content_disposition_header


def internal_file_download(file_field, *, download_name=None):
    """Return an X-Accel-Redirect response for a file under MEDIA_ROOT.

    Nginx must expose MEDIA_ROOT through an `internal` location named /uploads/.
    The path is checked against MEDIA_ROOT before it is sent to Nginx.
    """
    if not file_field or not getattr(file_field, "name", ""):
        raise Http404("File not found.")

    raw_name = file_field.name
    relative_path = Path(raw_name)
    if (
        relative_path.is_absolute()
        or "\\" in raw_name
        or any(part in {"", ".", ".."} for part in relative_path.parts)
    ):
        raise Http404("Invalid file path.")

    try:
        media_root = os.path.realpath(settings.MEDIA_ROOT)
        file_path = os.path.realpath(file_field.path)
        if os.path.commonpath((media_root, file_path)) != media_root:
            raise Http404("File is outside the private media directory.")
        if not os.path.isfile(file_path):
            raise Http404("File not found.")
    except (AttributeError, NotImplementedError, ValueError, OSError):
        raise Http404("File is not available through the configured private storage.")

    filename = download_name or os.path.basename(raw_name)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    encoded_path = quote(raw_name.replace(os.sep, "/"), safe="/")

    response = HttpResponse(b"", content_type=content_type)
    response["X-Accel-Redirect"] = f"/uploads/{encoded_path}"
    response["Content-Disposition"] = content_disposition_header(True, filename)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
