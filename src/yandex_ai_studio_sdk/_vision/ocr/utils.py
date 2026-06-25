from __future__ import annotations

from yandex_ai_studio_sdk._exceptions import AIStudioConfigurationError

_MAGIC_BYTES: tuple[tuple[bytes, str], ...] = (
    (b'\xff\xd8\xff', 'image/jpeg'),
    (b'\x89PNG', 'image/png'),
    (b'%PDF', 'application/pdf'),
)


def detect_mime_type(content: bytes) -> str:
    """Detect MIME type from content magic bytes.

    Supports JPEG, PNG and PDF.

    :param content: Raw file bytes.
    :returns: MIME type string.
    :raises AIStudioConfigurationError: If the content format is not recognized.
    """
    for magic, mime_type in _MAGIC_BYTES:
        if content.startswith(magic):
            return mime_type

    raise AIStudioConfigurationError(
        'unable to detect MIME type from content: '
        'only JPEG, PNG and PDF are supported'
    )
