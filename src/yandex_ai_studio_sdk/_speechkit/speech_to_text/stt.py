# pylint: disable=arguments-renamed,no-name-in-module,protected-access,redefined-builtin
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Generic, Literal, TypeVar, Union, cast

from google.protobuf.empty_pb2 import Empty
from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import (
    AudioChunk, AudioFormatOptions, EouClassifierOptions, ExternalEouClassifier, LanguageRestrictionOptions,
    RecognitionClassifierOptions, RecognitionModelOptions, RecognizeFileRequest, SilenceChunk, SpeakerLabelingOptions,
    SpeechAnalysisOptions, StreamingOptions, StreamingRequest, StreamingResponse, SummarizationOptions
)
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import AsyncRecognizerStub, RecognizerStub

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._speechkit.enums import AudioFormat as AudioFormat_
from yandex_ai_studio_sdk._speechkit.enums import LanguageCode as LanguageCode_
from yandex_ai_studio_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._types.model import ModelAsyncMixin, ModelSyncMixin, ModelSyncStreamMixin
from yandex_ai_studio_sdk._types.operation import (
    AsyncOperation, BaseOperation, Operation, OperationTypeT, ProtoOperation
)
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync, run_sync_generator

from .bistream import AsyncSTTBidirectionalStream, STTBidirectionalStream, STTBidirectionalStreamTypeT
from .config import LanguageCodesInputType, RecognitionClassifiersInputType, SpeechToTextConfig
from .result import (
    AsyncDeferredSpeechToTextResult, DeferredSpeechToTextResult, DeferredSpeechToTextResultTypeT, SpeechToTextResult,
    SpeechToTextStreamingEvent
)
from .structures import EndOfUtteranceClassifier as EndOfUtteranceClassifier_
from .structures import LLMPostProcessing as LLMPostProcessing_
from .structures import RecognitionClassifier as RecognitionClassifier_
from .structures import SpeechAnalysis as SpeechAnalysis_
from .structures import TextNormalization as TextNormalization_

logger = get_logger(__name__)


DeferredSTTInputType = Union[str, bytes]
STTInputType = Union[bytes, Sequence[Union[bytes, int]]]


class BaseSpeechToText(
    Generic[STTBidirectionalStreamTypeT, OperationTypeT, DeferredSpeechToTextResultTypeT],
    ModelSyncMixin[SpeechToTextConfig, SpeechToTextResult],
    ModelSyncStreamMixin[SpeechToTextConfig, SpeechToTextStreamingEvent],
    ModelAsyncMixin[SpeechToTextConfig, DeferredSpeechToTextResultTypeT, OperationTypeT],
):
    """Speech To Text class which provides concrete methods for working with SpeechKit STT API
    and incapsulates speech recognition settings.
    """

    #: Link to :py:class:`yandex_ai_studio_sdk._speechkit.enums.AudioFormat`
    #: for more convenient access.
    AudioFormat = AudioFormat_
    #: Link to :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.RecognitionClassifier`
    #: for more convenient access.
    RecognitionClassifier = RecognitionClassifier_
    #: Link to :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.EndOfUtteranceClassifier`
    #: for more convenient access.
    EndOfUtteranceClassifier = EndOfUtteranceClassifier_
    #: Link to :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.LLMPostProcessing`
    #: for more convenient access.
    LLMPostProcessing = LLMPostProcessing_
    #: Link to :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.SpeechAnalysis`
    #: for more convenient access.
    SpeechAnalysis = SpeechAnalysis_
    #: Link to :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.TextNormalization`
    #: for more convenient access.
    TextNormalization = TextNormalization_
    #: Link to :py:class:`yandex_ai_studio_sdk._speechkit.enums.LanguageCode`
    #: for more convenient access.
    LanguageCode = LanguageCode_

    _config_type = SpeechToTextConfig
    _result_type = SpeechToTextResult
    _bistream_type: type[STTBidirectionalStreamTypeT]
    _operation_impl: type[OperationTypeT]
    _deferred_result_impl: type[DeferredSpeechToTextResultTypeT]
    _proto_result_type = StreamingResponse

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        audio_format: UndefinedOrEnumWithUnknownInput[AudioFormat_] | None = UNDEFINED,
        model: UndefinedOr[str] | None = UNDEFINED,
        language_codes: UndefinedOr[LanguageCodesInputType] | None = UNDEFINED,
        text_normalization: UndefinedOr[TextNormalization_ | bool] | None = UNDEFINED,
        eou_classifier: UndefinedOr[EndOfUtteranceClassifier_ | bool] | None= UNDEFINED,
        recognition_classifiers: (
            UndefinedOr[RecognitionClassifiersInputType | bool] | None
        ) = UNDEFINED,
        speech_analysis: UndefinedOr[SpeechAnalysis_] | None = UNDEFINED,
        speaker_labeling: UndefinedOr[bool] | None = UNDEFINED,
        llm_post_process: UndefinedOr[LLMPostProcessing_] | None = UNDEFINED,
    ) -> Self:
        """
        Returns the new object with config fields overrode by passed values.

        To return set value back to default, pass `None` value.

        To learn more about parameters and their formats and possible values,
        refer to
        `STT documentation <https://yandex.cloud/docs/speechkit/stt>`_

        :param audio_format: Specifies the input audio format.
        :param model: The name of the STT model to use for recognition.
            See the list of available models and versions
            `in the documentation <https://yandex.cloud/docs/speechkit/stt/models>`_.
        :param language_codes: The list of `language codes <https://yandex.cloud/docs/speechkit/stt/models>`_
            to restrict recognition in the case of an automatic model, or a single language code.
        :param text_normalization:
            `Text normalization options <https://yandex.cloud/docs/speechkit/stt/normalization>`_:

            * ``True`` — turn on text normalization with default parameters;
            * ``False`` — turn text normalization off;
            * :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.TextNormalization`
              instance — text normalization with custom parameters;
            * ``None`` — for server default.
        :param eou_classifier:
            Configuration for `end of utterance detection model <https://yandex.cloud/docs/speechkit/stt/eou>`_:

            * ``True`` — use default EOU classifier;
            * ``False`` — disable EOU classifier ("external EOU classifier" in documentation);
            * :py:class:`yandex_ai_studio_sdk._speechkit.speech_to_text.structures.EndOfUtteranceClassifier`
              instance — use custom EOU classifier settings;
            * ``None`` — for server default.
        :param recognition_classifiers: Classifier or list of
            `classifiers for speech recognition <https://yandex.cloud/docs/speechkit/stt/analysis#classifier>`_.
        :param speech_analysis: Configuration for
            `speech analysis over speech recognition <https://yandex.cloud/docs/speechkit/stt/analysis#statistics>`_.
        :param speaker_labeling: Configuration for
            `speaker labeling <https://yandex.cloud/docs/speechkit/stt/speaker-labeling>`_.
        :param llm_post_process: Configuration for
            `LLM recognition results processing <https://yandex.cloud/docs/speechkit/stt/llm-results>`_.
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

    def _create_recognition_model_options(self, mode: Literal['real_time', 'full_data']) -> RecognitionModelOptions:
        c = self._config

        language_restriction = LanguageRestrictionOptions(
            language_code=LanguageCode_._coerce_to_proto(c.language_codes),
            restriction_type=LanguageRestrictionOptions.LanguageRestrictionType.WHITELIST,
        ) if c.language_codes else None

        text_normalization = TextNormalization_._coerce_to_proto(
            self._sdk,
            TextNormalization_._coerce(c.text_normalization),
        )

        audio_processing_type = {
            'real_time': RecognitionModelOptions.AudioProcessingType.REAL_TIME,
            'full_data': RecognitionModelOptions.AudioProcessingType.FULL_DATA,
        }[mode]

        return RecognitionModelOptions(
            audio_format=AudioFormat_._to_proto(AudioFormatOptions, c.audio_format),  # type: ignore[arg-type]
            audio_processing_type=audio_processing_type,
            language_restriction=language_restriction,
            model=c.model or '',
            text_normalization=text_normalization,
        )

    def _create_speech_analysis(self) -> SpeechAnalysisOptions | None:
        return SpeechAnalysis_._coerce_to_proto(self._sdk, self._config.speech_analysis)

    def _create_speaker_labeling(self) -> SpeakerLabelingOptions:
        speaker_labeling = {
            True: SpeakerLabelingOptions.SpeakerLabeling.SPEAKER_LABELING_ENABLED,
            False: SpeakerLabelingOptions.SpeakerLabeling.SPEAKER_LABELING_DISABLED,
            None: SpeakerLabelingOptions.SpeakerLabeling.SPEAKER_LABELING_UNSPECIFIED,
        }[self._config.speaker_labeling]
        return SpeakerLabelingOptions(speaker_labeling=speaker_labeling)

    def _create_summarization(self) -> SummarizationOptions | None:
        return LLMPostProcessing_._coerce_to_proto(self._sdk, self._config.llm_post_process)

    def _create_classifiers(self) -> RecognitionClassifierOptions:
        classifiers = None
        if raw_classifiers := self._config.recognition_classifiers:
            list_classifiers: list[RecognitionClassifier_]
            if isinstance(raw_classifiers, RecognitionClassifier_):
                list_classifiers = [raw_classifiers]
            else:
                list_classifiers = list(raw_classifiers)

            classifiers = [c._to_proto(self._sdk) for c in list_classifiers]
        return RecognitionClassifierOptions(
            classifiers=classifiers,
        )

    # pylint: disable-next=too-many-locals
    def _create_streaming_options(
        self,
        mode: Literal['real_time', 'full_data'],
    ) -> StreamingOptions:
        c = self._config

        eou_classifier: EouClassifierOptions | None = None
        if eou := c.eou_classifier:  # EndOfUtteranceClassifier or True
            assert isinstance(eou, (bool, EndOfUtteranceClassifier_))
            eou_classifier = EouClassifierOptions(
                default_classifier=EndOfUtteranceClassifier_._coerce_to_proto(
                    self._sdk,
                    EndOfUtteranceClassifier_._coerce(eou),
                )
            )
        elif c.eou_classifier is False:
            eou_classifier = EouClassifierOptions(
                external_classifier=ExternalEouClassifier()
            )

        return StreamingOptions(
            recognition_model=self._create_recognition_model_options(mode),
            eou_classifier=eou_classifier,
            recognition_classifier=self._create_classifiers(),
            speaker_labeling=self._create_speaker_labeling(),
            speech_analysis=self._create_speech_analysis(),
            summarization=self._create_summarization(),
        )

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
        options = self._create_streaming_options(mode=mode)
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

        return self._result_type._from_proto_iterable(
            proto=result,
            sdk=self._sdk,
        )

    async def _deferred_result_transformer(
        self,
        proto_result: Empty,  # pylint: disable=unused-argument
        timeout: float,
        ctx: BaseOperation.Context
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

        request = RecognizeFileRequest(
            recognition_classifier=self._create_classifiers(),
            recognition_model=self._create_recognition_model_options('full_data'),
            speaker_labeling=self._create_speaker_labeling(),
            speech_analysis=self._create_speech_analysis(),
            summarization=self._create_summarization(),
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

        return self._operation_impl(
            sdk=self._sdk,
            id=response.id ,
            proto_result_type=self._proto_result_type,
            result_type=SpeechToTextResult,
            transformer=self._deferred_result_transformer,
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
            )

    def create_bistream(self, *, timeout: float = 10 * 60) -> STTBidirectionalStreamTypeT:
        """Creates a bidirectional stream object for using
        `Yandex SpeechKit Streaming speech recognition <https://yandex.cloud/docs/speechkit/stt/streaming>`_.

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
    ]
):
    _bistream_type = AsyncSTTBidirectionalStream
    _operation_impl = AsyncOperation[AsyncDeferredSpeechToTextResult]
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
    ) -> AsyncOperation[SpeechToTextResult]:
        return await self._run_deferred(input=input, timeout=timeout)

    @doc_from(BaseSpeechToText._attach_deferred)
    async def attach_deferred(
        self,
        operation_id: str,
        timeout: float = 60
    ) -> AsyncOperation[AsyncDeferredSpeechToTextResult]:
        return await self._attach_deferred(operation_id=operation_id, timeout=timeout)


@doc_from(BaseSpeechToText)
class SpeechToText(
    BaseSpeechToText[
        STTBidirectionalStream,
        Operation[DeferredSpeechToTextResult],
        DeferredSpeechToTextResult,
    ]
):
    _bistream_type = STTBidirectionalStream
    _operation_impl = Operation[DeferredSpeechToTextResult]
    _deferred_result_impl = DeferredSpeechToTextResult
    __run = run_sync(BaseSpeechToText._run)
    __run_stream = run_sync_generator(BaseSpeechToText._run_stream)
    __run_deferred = run_sync(BaseSpeechToText._run_deferred)
    __attach_deferred = run_sync(BaseSpeechToText._attach_deferred)

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
    ) -> Operation[SpeechToTextResult]:
        return self.__run_deferred(input=input, timeout=timeout)

    @doc_from(BaseSpeechToText._attach_deferred)
    def attach_deferred(
        self,
        operation_id: str,
        timeout: float = 60
    ) -> AsyncOperation[AsyncDeferredSpeechToTextResult]:
        return self.__attach_deferred(operation_id=operation_id, timeout=timeout)

SpeechToTextTypeT = TypeVar('SpeechToTextTypeT', bound=BaseSpeechToText)
