from __future__ import annotations

from typing import Any

import pytest

from yandex_ai_studio_sdk._speechkit.enums import PCM16, AudioFormat, LanguageCode
from yandex_ai_studio_sdk._speechkit.speech_to_text.config import SpeechToTextConfig
from yandex_ai_studio_sdk.exceptions import AIStudioConfigurationError


def test_language_codes() -> None:
    config = SpeechToTextConfig(audio_format='mp3')

    for language_code in (
        'AUTO', 'auto',
        'ru_ru', 'ru-RU', 'RU_ru',
        LanguageCode.ru_RU
    ):
        config._replace(language_codes=language_code)
        config._replace(language_codes=[language_code])


def test_bad_language_codes() -> None:
    config = SpeechToTextConfig(audio_format='mp3')
    bad_value: Any
    for bad_value in (
        [],
        [[]],
        '',
        'RU_RU_RU',
        [{}],
        {},
    ):
        with pytest.raises(AIStudioConfigurationError):
            config._replace(language_codes=bad_value)


def test_audio_format() -> None:
    for audio_format in (
        'mp3',
        'MP3',
        AudioFormat.MP3,
        'PCM16(10)',
        'PCM16(10, 2)',
        AudioFormat.PCM16(1000)
    ):
        config = SpeechToTextConfig(audio_format=audio_format)
        config = config._replace(audio_format=audio_format)


def test_bad_audio_format() -> None:
    bad_value: Any
    for bad_value in (
        PCM16,
        'PCM16(10, 2, 3)'
        'PCM16(10, channels=3)',
        {},
        1000,
        'FOO'
    ):
        with pytest.raises(AIStudioConfigurationError):
            SpeechToTextConfig(audio_format=bad_value)

        with pytest.raises(AIStudioConfigurationError):
            config = SpeechToTextConfig(audio_format='mp3')
            config._replace(audio_format=bad_value)
