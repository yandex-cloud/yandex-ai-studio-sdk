# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

from typing import Generic

from typing_extensions import override
from yandex.cloud.ai.stt.v3.stt_pb2 import StreamingResponse
from yandex.cloud.ai.stt.v3.stt_service_pb2 import GetRecognitionRequest
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import AsyncRecognizerStub
from yandex_ai_studio_sdk._speechkit.enums import AudioFormat
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownInput
from yandex_ai_studio_sdk._types.function import BaseModelFunction
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import LanguageCodesInputType, RecognitionClassifiersInputType, SpeechToTextConfig
from .result import AsyncDeferredSpeechToTextResult, DeferredSpeechToTextResult, DeferredSpeechToTextResultTypeT
from .result.context import RequestDetails
from .structures import EndOfUtteranceClassifier, LLMPostProcessing, SpeechAnalysis, TextNormalization
from .stt import AsyncSpeechToText, SpeechToText, SpeechToTextTypeT
from .synonyms import SynonymsMixin


class BaseSpeechToTextFunction(
    Generic[SpeechToTextTypeT, DeferredSpeechToTextResultTypeT],
    BaseModelFunction[SpeechToTextTypeT],
    SynonymsMixin
):
    """Speech to Text function for creating speech recognition object which provides
    methods for invoking recognition.
    """

    _deferred_result_impl: type[DeferredSpeechToTextResultTypeT]

    @override
    # pylint: disable-next=too-many-locals
    def __call__(
        self,
        *,
        audio_format: EnumWithUnknownInput[AudioFormat],
        model: UndefinedOr[str] = UNDEFINED,
        language_codes: UndefinedOr[LanguageCodesInputType] = UNDEFINED,
        text_normalization: UndefinedOr[TextNormalization | bool] = UNDEFINED,
        eou_classifier: UndefinedOr[EndOfUtteranceClassifier | bool] = UNDEFINED,
        recognition_classifiers: UndefinedOr[RecognitionClassifiersInputType | bool] = UNDEFINED,
        speech_analysis: UndefinedOr[SpeechAnalysis] = UNDEFINED,
        speaker_labeling: UndefinedOr[bool] = UNDEFINED,
        llm_post_process: UndefinedOr[LLMPostProcessing] = UNDEFINED,
    ) -> SpeechToTextTypeT:
        """
        Creates SpeechToText object with provides methods for speech recognition.

        To learn more about parameters and their formats and possible values,
        refer to
        `STT docs <https://aistudio.yandex.ru/docs/speechkit/stt>`_

        :param audio_format: Specifies the input audio format.
        :param model: The name of the STT model to use for recognition.
            See the list of available models and versions in the
            `speech to text documentation <https://aistudio.yandex.ru/docs/speechkit/stt/models>`_.
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

        config = SpeechToTextConfig(
            audio_format=audio_format
        )

        stt = self._model_type(sdk=self._sdk, uri='<speechkit>', config=config)

        return stt.configure(
            model=model,
            language_codes=language_codes,
            text_normalization=text_normalization,
            eou_classifier=eou_classifier,
            recognition_classifiers=recognition_classifiers,
            speech_analysis=speech_analysis,
            speaker_labeling=speaker_labeling,
            llm_post_process=llm_post_process,
        )

    async def _get_recognition_result(
        self,
        operation_id: str,
        timeout: float = 60
    ) -> DeferredSpeechToTextResultTypeT:
        """Gets results of asynchronous recognition after finishing the operation."""
        request = GetRecognitionRequest(operation_id=operation_id)
        async with self._sdk._client.get_service_stub(AsyncRecognizerStub, timeout=timeout) as stub:
            result = []
            async for proto in self._sdk._client.call_service_stream(
                stub.GetRecognition,
                request,
                timeout=timeout,
                expected_type=StreamingResponse
            ):
                result.append(proto)

        return self._deferred_result_impl._from_proto_iterable_operation(
            proto=result,
            sdk=self._sdk,
            operation_id=operation_id,
            ctx=RequestDetails(model_config=None),
        )


@doc_from(BaseSpeechToTextFunction)
class SpeechToTextFunction(BaseSpeechToTextFunction[SpeechToText, DeferredSpeechToTextResult]):
    _model_type = SpeechToText
    _deferred_result_impl = DeferredSpeechToTextResult
    __get_recognition_result = run_sync(BaseSpeechToTextFunction._get_recognition_result)

    @doc_from(BaseSpeechToTextFunction._get_recognition_result)
    def get_recognition_result(
        self,
        operation_id: str,
        timeout: float = 60
    ) -> DeferredSpeechToTextResult:
        return self.__get_recognition_result(operation_id=operation_id, timeout=timeout)


@doc_from(BaseSpeechToTextFunction)
class AsyncSpeechToTextFunction(BaseSpeechToTextFunction[AsyncSpeechToText, AsyncDeferredSpeechToTextResult]):
    _model_type = AsyncSpeechToText
    _deferred_result_impl = AsyncDeferredSpeechToTextResult

    @doc_from(BaseSpeechToTextFunction._get_recognition_result)
    async def get_recognition_result(
        self,
        operation_id: str,
        timeout: float = 60
    ) -> AsyncDeferredSpeechToTextResult:
        return await self._get_recognition_result(operation_id=operation_id, timeout=timeout)
