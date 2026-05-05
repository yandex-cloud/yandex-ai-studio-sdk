from __future__ import annotations

from typing import Any

CLIENT_REQUEST_ID_METADATA_KEY = 'x-client-request-id'


def extract_client_request_id(metadata: Any) -> str | None:
    if not metadata:
        return None

    # grpc.aio.Metadata is iterable over (key, value) pairs, so the same code
    # also works for grpc metadata and tuple-like metadata containers.
    try:
        for key, value in metadata:
            if key != CLIENT_REQUEST_ID_METADATA_KEY:
                continue

            if isinstance(value, bytes):
                return value.decode('utf-8')
            return value
    except TypeError:
        return None

    return None
