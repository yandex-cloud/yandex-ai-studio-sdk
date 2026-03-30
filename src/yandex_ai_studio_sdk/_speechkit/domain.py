from __future__ import annotations

from yandex_ai_studio_sdk._types.domain import DomainWithFunctions
from yandex_ai_studio_sdk._utils.doc import doc_from

from .enums import AudioFormat as AudioFormat_
from .speech_to_text.function import AsyncSpeechToTextFunction, BaseSpeechToTextFunction, SpeechToTextFunction
from .text_to_speech.function import AsyncTextToSpeechFunction, BaseTextToSpeechFunction, TextToSpeechFunction


class BaseSpeechKitDomain(DomainWithFunctions):
    """
    Domain for working with `Yandex SpeechKit services <https://aistudio.yandex.ru/docs/speechkit/overview>`_.
    """

    #: Synonym for :py:class:`yandex_ai_studio_sdk._speechkit.enums.AudioFormat`
    AudioFormat = AudioFormat_

    #: API for `text to speech <https://aistudio.yandex.ru/docs/speechkit/tts/>`_ service
    text_to_speech: BaseTextToSpeechFunction
    #: Synonym for `text_to_speech` function
    tts: BaseTextToSpeechFunction

    #: API for `speech to text <https://aistudio.yandex.ru/docs/speechkit/stt/>`_ service
    speech_to_text: BaseSpeechToTextFunction
    #: Synonym for `speech_to_text` function
    stt: BaseSpeechToTextFunction


@doc_from(BaseSpeechKitDomain)
class AsyncSpeechKitDomain(BaseSpeechKitDomain):
    text_to_speech: AsyncTextToSpeechFunction
    tts: AsyncTextToSpeechFunction

    speech_to_text: AsyncSpeechToTextFunction
    stt: AsyncSpeechToTextFunction


@doc_from(BaseSpeechKitDomain)
class SpeechKitDomain(BaseSpeechKitDomain):
    text_to_speech: TextToSpeechFunction
    tts: TextToSpeechFunction

    speech_to_text: SpeechToTextFunction
    stt: SpeechToTextFunction
