from __future__ import annotations

DEFAULT_MAX_WORKERS = 4
"""Default maximum number of parallel upload workers"""

DEFAULT_SKIP_ON_ERROR = False
"""Default behavior for handling upload errors"""

DEFAULT_MAX_CHUNK_SIZE_TOKENS = 800
"""Default maximum chunk size in tokens (OpenAI uses 800 for auto strategy)"""

DEFAULT_CHUNK_OVERLAP_TOKENS = 400
"""Default chunk overlap in tokens (OpenAI uses 400 for auto strategy)"""

BYTES_PER_MB = 1024 * 1024
"""Bytes per megabyte for display"""

MAX_FILES_PER_INDEX_CREATE = 10_000
"""Maximum number of files per search index create request"""

DEFAULT_POLL_TIMEOUT = 3600
"""Default timeout in seconds for waiting on index creation operation"""
