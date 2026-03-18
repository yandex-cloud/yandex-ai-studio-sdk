from __future__ import annotations

from yandex_ai_studio_sdk._speechkit.enums import AudioFormat as AudioFormat_
from yandex_ai_studio_sdk._speechkit.enums import LanguageCode as LanguageCode_

from .structures import EndOfUtteranceClassifier as EndOfUtteranceClassifier_
from .structures import LLMPostProcessing as LLMPostProcessing_
from .structures import RecognitionClassifier as RecognitionClassifier_
from .structures import SpeechAnalysis as SpeechAnalysis_
from .structures import TextNormalization as TextNormalization_


class SynonymsMixin:
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
