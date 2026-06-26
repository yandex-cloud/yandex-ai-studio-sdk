# pylint: disable=arguments-renamed,no-name-in-module,protected-access,redefined-builtin
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Generic, Literal, TypeVar, Union, cast

from google.protobuf.empty_pb2 import Empty
from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import (
    AudioChunk, SilenceChunk, StreamingOptions, StreamingRequest, StreamingResponse
)
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import AsyncRecognizerStub, RecognizerStub

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._speechkit.enums import AudioFormat
from yandex_ai_studio_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._types.model import (
    ModelAsyncAttachMixin, ModelAsyncMixin, ModelSyncAttachMixin, ModelSyncMixin, ModelSyncStreamMixin
)
from yandex_ai_studio_sdk._types.operation import (
    AsyncOperation, Operation, OperationContext, OperationTypeT, ProtoOperation
)
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync, run_sync_generator

from .bistream import AsyncSTTBidirectionalStream, STTBidirectionalStream, STTBidirectionalStreamTypeT
from .config import LanguageCodesInputType, RecognitionClassifiersInputType, SpeechToTextConfig
from .result import (
    AsyncDeferredSpeechToTextResult, DeferredSpeechToTextResult, DeferredSpeechToTextResultTypeT, SpeechToTextResult,
    SpeechToTextStreamingEvent
)
from .result.context import RequestDetails
from .structures import EndOfUtteranceClassifier, LLMPostProcessing, SpeechAnalysis, TextNormalization
from .synonyms import SynonymsMixin
from .utils import create_recognize_file_request, create_streaming_options

logger = get_logger(__name__)


DeferredSTTInputType = Union[str, bytes]
STTInputType = Union[bytes, Sequence[Union[bytes, int]]]


class BaseSpeechToText(
    Generic[STTBidirectionalStreamTypeT, OperationTypeT, DeferredSpeechToTextResultTypeT],
    ModelSyncMixin[SpeechToTextConfig, SpeechToTextResult],
    ModelSyncStreamMixin[SpeechToTextConfig, SpeechToTextStreamingEvent],
    ModelAsyncMixin[SpeechToTextConfig, DeferredSpeechToTextResultTypeT, OperationTypeT],
    SynonymsMixin
):
    """Speech To Text class which provides concrete methods for working with SpeechKit STT API
    and incapsulates speech recognition settings.
    """

    _config_type = SpeechToTextConfig
    _result_type = SpeechToTextResult
    _bistream_type: type[STTBidirectionalStreamTypeT]
    _operation_type: type[OperationTypeT]
    _deferred_result_impl: type[DeferredSpeechToTextResultTypeT]
    _proto_result_type = StreamingResponse

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        audio_format: UndefinedOrEnumWithUnknownInput[AudioFormat] | None = UNDEFINED,
        model: UndefinedOr[str] | None = UNDEFINED,
        language_codes: UndefinedOr[LanguageCodesInputType] | None = UNDEFINED,
        text_normalization: UndefinedOr[TextNormalization | bool] | None = UNDEFINED,
        eou_classifier: UndefinedOr[EndOfUtteranceClassifier | bool] | None= UNDEFINED,
        recognition_classifiers: (
            UndefinedOr[RecognitionClassifiersInputType | bool] | None
        ) = UNDEFINED,
        speech_analysis: UndefinedOr[SpeechAnalysis] | None = UNDEFINED,
        speaker_labeling: UndefinedOr[bool] | None = UNDEFINED,
        llm_post_process: UndefinedOr[LLMPostProcessing] | None = UNDEFINED,
    ) -> Self:
        """
        Returns the new object with config fields overrode by passed values.

        To return set value back to default, pass `None` value.

        To learn more about parameters and their formats and possible values,
        refer to
        `STT documentation <https://aistudio.yandex.ru/docs/speechkit/stt>`_

        :param audio_format: Specifies the input audio format.
        :param model: The name of the STT model to use for recognition.
            See the list of available models and versions
            `in the documentation <https://aistudio.yandex.ru/docs/speechkit/stt/models>`_.
        :param language_codes: The list of `language codes <https://aistudio.yandex.ru/docs/speechkit/stt/models>`_
            to restrict recognition in the case of an automatic model, or a single language code.
        :param text_normalization:
            `Text normalization options <https://aistudio.yandex.ru/docs/speechkit/stt/normalization>`_:

            * ``True`` — turn on text normalization with default parameters;
            * ``False`` — turn text normalization off;
            * :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.TextNormalization`
              instance — text normalization with custom parameters;
            * ``None`` — for server default.
        :param eou_classifier:
            Configuration for `end of utterance detection model <https://aistudio.yandex.ru/docs/speechkit/stt/eou>`_:

            * ``True`` — use default EOU classifier;
            * ``False`` — disable EOU classifier ("external EOU classifier" in documentation);
            * :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.EndOfUtteranceClassifier`
              instance — use custom EOU classifier settings;
            * ``None`` — for server default.
        :param recognition_classifiers: Classifier or list of
            `classifiers for speech recognition <https://aistudio.yandex.ru/docs/speechkit/stt/analysis#classifier>`_.
        :param speech_analysis: Configuration for
            `speech analysis over speech recognition <https://aistudio.yandex.ru/docs/speechkit/stt/analysis#statistics>`_.
        :param speaker_labeling: Configuration for
            `speaker labeling <https://aistudio.yandex.ru/docs/speechkit/stt/speaker-labeling>`_.
        :param llm_post_process: Configuration for
            `LLM recognition results processing <https://aistudio.yandex.ru/docs/speechkit/stt/llm-results>`_.
            (Also known as Summarization in earlier documentation.)

        """

        return super().configure(
            audio_format=audio_format,
            model=model,
            language_codes=language_codes,
            text_normalization=text_normalization,
            eou_classifier=eou_classifier,
            recognition_classifiers=recognition_classifiers,
            speech_analysis=speech_analysis,
            speaker_labeling=speaker_labeling,
            llm_post_process=llm_post_process,
        )

    @override
    def __repr__(self) -> str:
        # STT doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'


    def _coerce_streaming_input(
        self,
        raw_input: STTInputType
    ) -> list[bytes | int]:
        input: Sequence[bytes | int]
        if isinstance(raw_input, bytes):
            input = [raw_input]
        elif (
            isinstance(raw_input, Sequence) and
            all(isinstance(el, (bytes, int)) for el in raw_input)
        ):
            input = list(raw_input)
        else:
            raise TypeError(
                'input for stt.run/stt.run_stream must contain a bytes or sequence of bytes | int elements')

        return input

    async def _stream_input_generator(
        self,
        options: StreamingOptions,
        input_list: list[bytes | int]
    ) -> AsyncIterator[StreamingRequest]:
        yield StreamingRequest(session_options=options)
        for element in input_list:
            if isinstance(element, bytes):
                yield StreamingRequest(
                    chunk=AudioChunk(data=element)
                )
            else:
                assert isinstance(element, int)
                yield StreamingRequest(
                    silence_chunk=SilenceChunk(duration_ms=element)
                )

    async def _run_stream_impl(
        self,
        raw_input: STTInputType,
        timeout: float,
        mode: Literal['real_time', 'full_data'],
    ) -> AsyncIterator[StreamingResponse]:
        options = create_streaming_options(
            sdk=self._sdk,
            config=self._config,
            mode=mode
        )
        input_list = self._coerce_streaming_input(raw_input)

        async with self._client.get_service_stub(RecognizerStub, timeout=timeout) as stub:
            async for response in self._client.stream_service_stream(
                stub.RecognizeStreaming,
                requests=self._stream_input_generator(options, input_list),
                timeout=timeout,
                expected_type=StreamingResponse
            ):
                yield response

    @override
    async def _run(
        self,
        input: STTInputType,
        *,
        timeout: float = 60,
    ) -> SpeechToTextResult:
        """Run a speech recognition for given `input` and return joined result.

        To change initial stt settings use ``.configure`` method:

        >>> stt = sdk.speechkit.speech_to_text(audio_format='mp3')
        >>> stt = stt.configure(audio_format='WAV')

        :param input:
            In case of bytes input, input treated as an audio-data.
            In case of bytes/int sequence, input treated as chunks of audio data with integers for silence chunks.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: recognition result
        """

        result = []
        async for proto in self._run_stream_impl(
            raw_input=input,
            timeout=timeout,
            mode='full_data',
        ):
            result.append(proto)

        ctx = RequestDetails(
            model_config=self._config,
        )

        return self._result_type._from_proto_iterable(
            proto=result,
            sdk=self._sdk,
            ctx=ctx,
        )

    async def _operation_transformer(
        self,
        proto_result: Empty,  # pylint: disable=unused-argument
        timeout: float,
        ctx: OperationContext
    ) -> DeferredSpeechToTextResultTypeT:
        result = cast(
            DeferredSpeechToTextResultTypeT,
            await self._sdk.speechkit.speech_to_text._get_recognition_result(
                timeout=timeout,
                operation_id=ctx.id
            )
        )
        return result

    @override
    async def _run_deferred(
        self,
        input: DeferredSTTInputType,
        *,
        timeout: float = 60,
    ) -> OperationTypeT:
        """Run a speech recognition for given `input` and return operation object
        to track progress of recognition and result retrieval.

        To change initial stt settings use ``.configure`` method:

        >>> stt = sdk.speechkit.speech_to_text(audio_format='mp3')
        >>> stt = stt.configure(audio_format='WAV')

        :param input:
            In case of bytes input, input treated as an audio-data.
            In case of str input, input treated as a S3 url.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: Operation object.
        """

        request = create_recognize_file_request(
            sdk=self._sdk,
            config=self._config
        )
        if isinstance(input, str):
            request.uri = input
        elif isinstance(input, bytes):
            request.content = input
        else:
            raise TypeError('input for stt.run_deferred must be a str with s3 uri or bytes with audio data')


        async with self._client.get_service_stub(AsyncRecognizerStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.RecognizeFile,
                request=request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )

        return self._operation_type(
            sdk=self._sdk,
            id=response.id ,
            proto_result_type=self._proto_result_type,
            result_type=SpeechToTextResult,
            transformer=self._operation_transformer,
        )

    @override
    async def _run_stream(
        self,
        input: STTInputType,
        *,
        timeout: float = 60,
    ) -> AsyncIterator[SpeechToTextStreamingEvent]:
        """Run a speech recognition for given `input`; method have an iterator return.

        To change initial stt settings use ``.configure`` method:

        >>> stt = sdk.speechkit.speech_to_text(audio_format='mp3')
        >>> stt = stt.configure(audio_format='WAV')

        :param input:
            In case of bytes input, input treated as an audio-data.
            In case of bytes/int sequence, input treated as chunks of audio data with integers for silence chunks.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: recognition result
        """

        async for proto in self._run_stream_impl(
            raw_input=input,
            timeout=timeout,
            mode='real_time',
        ):
            yield SpeechToTextStreamingEvent._from_proto(
                proto=proto,
                sdk=self._sdk,
                ctx=RequestDetails(
                    model_config=self._config,
                )
            )

    def create_bistream(self, *, timeout: float = 10 * 60) -> STTBidirectionalStreamTypeT:
        """Creates a bidirectional stream object for using
        `Yandex SpeechKit Streaming speech recognition <https://aistudio.yandex.ru/docs/speechkit/stt/streaming>`_.

        :param timeout: GRPC timeout in seconds that defines the maximum lifetime of the entire stream.
            The timeout countdown begins from the moment of the first stream interaction.
        """

        return self._bistream_type(
            sdk=self._sdk,
            config=self._config,
            timeout=timeout
        )


class AsyncSpeechToText(
    BaseSpeechToText[
        AsyncSTTBidirectionalStream,
        AsyncOperation[AsyncDeferredSpeechToTextResult],
        AsyncDeferredSpeechToTextResult,
    ],
    ModelAsyncAttachMixin[AsyncOperation[AsyncDeferredSpeechToTextResult]],
):
    _bistream_type = AsyncSTTBidirectionalStream
    _operation_type = AsyncOperation[AsyncDeferredSpeechToTextResult]
    _deferred_result_impl = AsyncDeferredSpeechToTextResult

    @doc_from(BaseSpeechToText._run)
    async def run(
        self,
        input: STTInputType,
        *,
        timeout: float = 60
    ) -> SpeechToTextResult:
        return await self._run(input=input, timeout=timeout)

    @doc_from(BaseSpeechToText._run_stream)
    async def run_stream(
        self,
        input: STTInputType,
        *,
        timeout: float = 60
    ) -> AsyncIterator[SpeechToTextStreamingEvent]:
        async for chunk in self._run_stream(input=input, timeout=timeout):
            yield chunk

    @doc_from(BaseSpeechToText._run_deferred)
    async def run_deferred(
        self,
        input: DeferredSTTInputType,
        *,
        timeout: float = 60
    ) -> AsyncOperation[AsyncDeferredSpeechToTextResult]:
        return await self._run_deferred(input=input, timeout=timeout)


@doc_from(BaseSpeechToText)
class SpeechToText(
    BaseSpeechToText[
        STTBidirectionalStream,
        Operation[DeferredSpeechToTextResult],
        DeferredSpeechToTextResult,
    ],
    ModelSyncAttachMixin[Operation[DeferredSpeechToTextResult]],
):
    _bistream_type = STTBidirectionalStream
    _operation_type = Operation[DeferredSpeechToTextResult]
    _deferred_result_impl = DeferredSpeechToTextResult
    __run = run_sync(BaseSpeechToText._run)
    __run_stream = run_sync_generator(BaseSpeechToText._run_stream)
    __run_deferred = run_sync(BaseSpeechToText._run_deferred)
    @doc_from(BaseSpeechToText._run)
    def run(
        self,
        input: STTInputType,
        *,
        timeout: float = 60
    ) -> SpeechToTextResult:
        return self.__run(input=input, timeout=timeout)

    @doc_from(BaseSpeechToText._run_stream)
    def run_stream(
        self,
        input: STTInputType,
        *,
        timeout: float = 60
    ) -> Iterator[SpeechToTextStreamingEvent]:
        yield from self.__run_stream(input=input, timeout=timeout)

    @doc_from(BaseSpeechToText._run_deferred)
    def run_deferred(
        self,
        input: DeferredSTTInputType,
        *,
        timeout: float = 60
    ) -> Operation[DeferredSpeechToTextResult]:
        return self.__run_deferred(input=input, timeout=timeout)

SpeechToTextTypeT = TypeVar('SpeechToTextTypeT', bound=BaseSpeechToText)
