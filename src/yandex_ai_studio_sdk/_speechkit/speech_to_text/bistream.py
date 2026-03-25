# pylint: disable=no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

from typing import TypeVar

from yandex.cloud.ai.stt.v3.stt_pb2 import AudioChunk, Eou, SilenceChunk, StreamingRequest, StreamingResponse
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import RecognizerStub
from yandex_ai_studio_sdk._speechkit.bistream import (
    AsyncBidirectionalStreamMixin, BaseBidirectionalStream, BidirectionalStreamMixin
)
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import SpeechToTextConfig
from .result import SpeechToTextStreamingEvent
from .utils import create_streaming_options


class BaseSTTBidirectionalStream(
    BaseBidirectionalStream[
        SpeechToTextConfig,
        SpeechToTextStreamingEvent,
        StreamingRequest,
        StreamingResponse,
        RecognizerStub,
        bytes,
    ]
):
    """Bidirectional SpeechKit  API which allows to write requests and read synthesized result
    in realtime"""

    _stub_class = RecognizerStub
    _result_class = SpeechToTextStreamingEvent

    async def _create_call(self, timeout: float):
        async with self._client.get_service_stub(self._stub_class, timeout=timeout) as stub:
            return await self._client.stream_stream_call(
                stub.RecognizeStreaming,
                timeout=timeout
            )

    def _create_stream_options(self) -> StreamingRequest:
        options = create_streaming_options(
            sdk=self._sdk,
            config=self._config,
            mode='real_time',
        )

        return StreamingRequest(
            session_options=options
        )

    def _create_request(self, input: bytes) -> StreamingRequest:
        return StreamingRequest(
            chunk=AudioChunk(data=input)
        )

    async def _write_silence(self, duration_ms: int) -> None:
        """Send payload with silence to not to send useless bytes with silence"""

        request = StreamingRequest(
            silence_chunk=SilenceChunk(
                duration_ms=duration_ms
            )
        )
        await self._write_request(request)

    async def _write_end_of_utterance(self) -> None:
        """Send end of utterance signal in case of disabled end of utterance classifier
        (or "external" end of utterance classifier according to the backend documentation)
        """

        request = StreamingRequest(
            eou=Eou()
        )
        await self._write_request(request)


class AsyncSTTBidirectionalStream(
    BaseSTTBidirectionalStream,
    AsyncBidirectionalStreamMixin[
        SpeechToTextConfig,
        SpeechToTextStreamingEvent,
        StreamingRequest,
        StreamingResponse,
        RecognizerStub,
        str,
    ]
):
    __doc__ = BaseSTTBidirectionalStream.__doc__

    @doc_from(BaseSTTBidirectionalStream._write_silence)
    async def write_silence(self, duration_ms: int) -> None:
        await self._write_silence(duration_ms)

    @doc_from(BaseSTTBidirectionalStream._write_end_of_utterance)
    async def write_end_of_utterance(self) -> None:
        await self._write_end_of_utterance()

    eou = write_end_of_utterance


class STTBidirectionalStream(
    BaseSTTBidirectionalStream,
    BidirectionalStreamMixin[
        SpeechToTextConfig,
        SpeechToTextStreamingEvent,
        StreamingRequest,
        StreamingResponse,
        RecognizerStub,
        str,
    ]
):
    __doc__ = BaseSTTBidirectionalStream.__doc__
    __write_silence = run_sync(BaseSTTBidirectionalStream._write_silence)
    __write_end_of_utterance = run_sync(BaseSTTBidirectionalStream._write_end_of_utterance)

    @doc_from(BaseSTTBidirectionalStream._write_silence)
    def write_silence(self, duration_ms: int) -> None:
        self.__write_silence(duration_ms)

    @doc_from(BaseSTTBidirectionalStream._write_end_of_utterance)
    def write_end_of_utterance(self) -> None:
        self.__write_end_of_utterance()

    eou = write_end_of_utterance


STTBidirectionalStreamTypeT = TypeVar('STTBidirectionalStreamTypeT', bound=BaseSTTBidirectionalStream)
