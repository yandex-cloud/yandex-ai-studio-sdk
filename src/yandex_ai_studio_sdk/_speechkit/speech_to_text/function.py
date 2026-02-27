from __future__ import annotations

from typing_extensions import override

from yandex_ai_studio_sdk._speechkit.enums import AudioFormat
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownInput
from yandex_ai_studio_sdk._types.function import BaseModelFunction
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._utils.doc import doc_from

from .config import LanguageCodesInputType, RecognitionClassifiersInputType, SpeechToTextConfig
from .structures import EndOfUtteranceClassifier, LLMPostProcessing, SpeechAnalysis, TextNormalization
from .stt import AsyncSpeechToText, SpeechToText, SpeechToTextTypeT


class BaseSpeechToTextFunction(BaseModelFunction[SpeechToTextTypeT]):
    """Speech to Text function for creating speech recognition object which provides
    methods for invoking recognition.
    """

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
        `STT docs <https://yandex.cloud/docs/speechkit/stt>`_

        :param audio_format: Specifies the input audio format.
        :param model: The name of the STT model to use for recognition.
            See the list of available models and versions in the
            `speech to text documentation <https://yandex.cloud/docs/speechkit/stt/models>`_.
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


@doc_from(BaseSpeechToTextFunction)
class SpeechToTextFunction(BaseSpeechToTextFunction[SpeechToText]):
    _model_type = SpeechToText


@doc_from(BaseSpeechToTextFunction)
class AsyncSpeechToTextFunction(BaseSpeechToTextFunction[AsyncSpeechToText]):
    _model_type = AsyncSpeechToText
