from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Union

from typing_extensions import override

from yandex_ai_studio_sdk._exceptions import AIStudioConfigurationError
from yandex_ai_studio_sdk._speechkit.enums import AudioFormat, LanguageCode, LanguageCodesInputType
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownInput
from yandex_ai_studio_sdk._types.model_config import BaseModelConfig

from .structures import (
    EndOfUtteranceClassifier, LLMPostProcessing, RecognitionClassifier, SpeechAnalysis, TextNormalization
)

RecognitionClassifiersInputType = Union[RecognitionClassifier, Sequence[RecognitionClassifier]]


@dataclass(frozen=True)
class SpeechToTextConfig(BaseModelConfig):
    """Object to hold speech to text run configuration"""

    #: Specifies input audio format.
    audio_format: EnumWithUnknownInput[AudioFormat]

    #: The name of the STT model to use for recognition.
    #: Look for available model and versions
    #: `in documentation <https://aistudio.yandex.ru/docs/speechkit/stt/models>`_.
    model: str | None = None

    #: The list of `language codes <https://aistudio.yandex.ru/docs/speechkit/stt/models>`_
    #: to restrict recognition in the case of an auto model (or just one language code).
    language_codes: LanguageCodesInputType | None = None

    #: `Text normalization options <https://aistudio.yandex.ru/docs/speechkit/stt/normalization>`_:
    #:
    #: * ``True`` for turning on text normalization with default parameters;
    #: * ``False`` for turning text normalization off;
    #: * :py:class:`~.TextNormalization` instance for text normaliztion with non-default parameters;
    #: * Nothing for server default.
    text_normalization: TextNormalization | bool | None = None

    #: Configuration for an `end of utterance detection model <https://aistudio.yandex.ru/docs/speechkit/stt/eou>`_:
    #:
    #: * ``True`` for default eou classifier;
    #: * ``False`` for no eou classifier (documentation describes it as "external eou classifier";
    #: * Instance of :py:class:`~.EndOfUtteranceClassifier` with eou classifier settings;
    #: * Nothing for server default.
    eou_classifier: EndOfUtteranceClassifier | bool | None = None

    #: Classifier or list of
    #: `classifiers over speech recognition <https://aistudio.yandex.ru/docs/speechkit/stt/analysis#classifier>`_.
    recognition_classifiers: RecognitionClassifiersInputType | None = None

    #: Configuration for
    #: `speech analysis over speech recognition <https://aistudio.yandex.ru/docs/speechkit/stt/analysis#statistics>`_.
    speech_analysis: SpeechAnalysis | None = None

    #: Configuration for `speaker labeling <https://aistudio.yandex.ru/docs/speechkit/stt/speaker-labeling>`_.
    speaker_labeling: bool | None = None

    #: Configuration for
    #: `LLM recognition results processing <https://aistudio.yandex.ru/docs/speechkit/stt/llm-results>`_.
    #: At some point in history also known as ``Summarization``.
    llm_post_process: LLMPostProcessing | None = None

    @override
    def _validate_configure(self) -> None:
        self._validate_language_codes()

        try:
            AudioFormat._coerce(self.audio_format)
        except (ValueError, TypeError) as e:
            raise AIStudioConfigurationError(
                f'get bad value {self.audio_format} as audio_format config option'
            ) from e

    def _validate_language_codes(self) -> None:
        if self.language_codes is None:
            return

        language_codes: Sequence[str | LanguageCode]
        if isinstance(self.language_codes, (str, LanguageCode)):
            language_codes = [self.language_codes]
        else:
            language_codes = self.language_codes

        if not isinstance(language_codes, Sequence):
            raise AIStudioConfigurationError(
                'language_codes configuration parameter could be only '
                'str, LanguageCode or sequence of either, '
                f'got {self.language_codes}'
            )

        if not language_codes:
            raise AIStudioConfigurationError("language_codes configuration parameter can't be empty")

        for language_code in language_codes:
            try:
                LanguageCode._coerce_to_str(language_code)
            except (TypeError, ValueError) as e:
                raise AIStudioConfigurationError(
                    f'got bad value {language_code} in language_codes configuration parameter'
                ) from e
