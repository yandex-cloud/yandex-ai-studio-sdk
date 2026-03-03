# pylint: disable=no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TypeVar

from yandex_ai_studio_sdk._types.proto import SDKType

from .config import SpeechToTextConfig
from .result import SpeechToTextResult


class BaseSTTBidirectionalStream:
    """Bidirectional SpeechKit STT API which allows to write requests and read recognized result
    in realtime"""

    def __init__(
        self,
        *,
        sdk: SDKType,
        config: SpeechToTextConfig,
        timeout: float,
    ):
        self._sdk = sdk
        self._config = config
        self._timeout = timeout


class AsyncSTTBidirectionalStream(BaseSTTBidirectionalStream, AsyncIterator[SpeechToTextResult]):
    __doc__ = BaseSTTBidirectionalStream.__doc__

    async def __anext__(self) -> SpeechToTextResult:
        """Same as ``.read``, but makes AsyncSTTBidirectionalStream
        eligible to be used as AsyncIterator."""

        return SpeechToTextResult(_sdk=self._sdk)

    def __aiter__(self) -> AsyncIterator[SpeechToTextResult]:
        return self


class STTBidirectionalStream(BaseSTTBidirectionalStream, Iterator[SpeechToTextResult]):
    def __next__(self) -> SpeechToTextResult:
        """Same as ``.read``, but makes STTBidirectionalStream
        eligible to be used as Iterator."""

        return SpeechToTextResult(_sdk=self._sdk)


STTBidirectionalStreamTypeT = TypeVar('STTBidirectionalStreamTypeT', bound=BaseSTTBidirectionalStream)
