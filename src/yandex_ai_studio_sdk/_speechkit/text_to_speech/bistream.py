# pylint: disable=no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

from typing import TypeVar

from yandex.cloud.ai.tts.v3.tts_pb2 import (
    AudioFormatOptions, ForceSynthesisEvent, StreamSynthesisRequest, StreamSynthesisResponse, SynthesisInput,
    SynthesisOptions
)
from yandex.cloud.ai.tts.v3.tts_service_pb2_grpc import SynthesizerStub
from yandex_ai_studio_sdk._speechkit.bistream import (
    AsyncBidirectionalStreamMixin, BaseBidirectionalStream, BidirectionalStreamMixin
)
from yandex_ai_studio_sdk._speechkit.enums import AudioFormat
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import TextToSpeechConfig
from .result import TextToSpeechResult


class BaseTTSBidirectionalStream(
    BaseBidirectionalStream[
        TextToSpeechConfig,
        TextToSpeechResult,
        StreamSynthesisRequest,
        StreamSynthesisResponse,
        SynthesizerStub,
        str,
    ]
):
    """Bidirectional SpeechKit TTS API which allows to write requests and read synthesized result
    in realtime"""

    _stub_class = SynthesizerStub
    _result_class = TextToSpeechResult

    async def _create_call(self, timeout: float):
        async with self._client.get_service_stub(self._stub_class, timeout=timeout) as stub:
            return await self._client.stream_stream_call(
                stub.StreamSynthesis,
                timeout=timeout
            )

    def _create_stream_options(self) -> StreamSynthesisRequest:
        c = self._config

        options = SynthesisOptions(
            loudness_normalization_type=c.loudness_normalization,  # type: ignore[arg-type]
            model=c.model or "",
            output_audio_spec=AudioFormat._to_proto(AudioFormatOptions, c.audio_format),
            pitch_shift=c.pitch_shift,  # type: ignore[arg-type]
            role=c.role,  # type: ignore[arg-type]
            speed=c.speed,  # type: ignore[arg-type]
            voice=c.voice,  # type: ignore[arg-type]
            volume=c.volume,  # type: ignore[arg-type]
        )

        return StreamSynthesisRequest(
            options=options
        )

    def _create_request(self, input: str) -> StreamSynthesisRequest:
        return StreamSynthesisRequest(
            synthesis_input=SynthesisInput(text=input)
        )

    async def _flush(self) -> None:
        """Send message to server to force synthesis with already given input"""

        request = StreamSynthesisRequest(
            force_synthesis=ForceSynthesisEvent()
        )
        await self._write_request(request)


class AsyncTTSBidirectionalStream(
    BaseTTSBidirectionalStream,
    AsyncBidirectionalStreamMixin[
        TextToSpeechConfig,
        TextToSpeechResult,
        StreamSynthesisRequest,
        StreamSynthesisResponse,
        SynthesizerStub,
        str,
    ]
):
    __doc__ = BaseTTSBidirectionalStream.__doc__

    @doc_from(BaseTTSBidirectionalStream._flush)
    async def flush(self) -> None:
        await self._flush()


class TTSBidirectionalStream(
    BaseTTSBidirectionalStream,
    BidirectionalStreamMixin[
        TextToSpeechConfig,
        TextToSpeechResult,
        StreamSynthesisRequest,
        StreamSynthesisResponse,
        SynthesizerStub,
        str,
    ]
):
    __doc__ = BaseTTSBidirectionalStream.__doc__
    __flush = run_sync(BaseTTSBidirectionalStream._flush)

    @doc_from(BaseTTSBidirectionalStream._flush)
    def flush(self) -> None:
        self.__flush()


TTSBidirectionalStreamTypeT = TypeVar('TTSBidirectionalStreamTypeT', bound=BaseTTSBidirectionalStream)
