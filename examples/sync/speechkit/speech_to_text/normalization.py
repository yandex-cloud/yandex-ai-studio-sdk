#!/usr/bin/env python3
"""
Example on how to use text normalization
"""

from __future__ import annotations

from yandex_ai_studio_sdk import AIStudio

SAMPLERATE = 44100


def get_voice_data(sdk: AIStudio, request: str) -> bytes:
    """TTS is just a random source of voice data and it is not related to this example in any way."""
    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    tts_result = tts.run(request)
    return tts_result.data


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

    stt = sdk.speechkit.speech_to_text(
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
        language_codes='ru_RU',
        text_normalization=True,  # True is just turning it on
    )

    # with phone normalization (default)
    request_text = 'Мой телефон - +7 499 646-00-32'
    voice_data = get_voice_data(sdk, request_text)
    result = stt.run(voice_data)
    print(f"{result.final_text=} {result.final_refinement_text=}")
    # note that .text helper will return final_refiniment text if it exists
    assert result.text == result.final_refinement_text

    # without phone normalization
    stt = stt.configure(
        text_normalization=stt.TextNormalization(phone_formatting=False)
    )
    result = stt.run(voice_data)
    request_text = 'Мой телефон - +7 499 646-00-32'
    voice_data = get_voice_data(sdk, request_text)
    result = stt.run(voice_data)
    print(f"{result.final_text=} {result.final_refinement_text=}")

    # profanity filter:
    request_text = 'Сударь, вы - мудак!'
    voice_data = get_voice_data(sdk, request_text)
    stt = stt.configure(
        # instead of bool you could pass a special normalization settings object
        text_normalization=stt.TextNormalization(profanity_filter=True)
    )
    result = stt.run(voice_data)
    print(f"{result.final_text=} {result.final_refinement_text=}")

    # literature text:
    request_text = 'Этот тест не имеет запятых но в обработанном тексте они будут'
    voice_data = get_voice_data(sdk, request_text)
    stt = stt.configure(
        text_normalization=stt.TextNormalization(literature_text=True)
    )
    result = stt.run(voice_data)
    print(f"{result.final_text=} {result.final_refinement_text=}")


if __name__ == '__main__':
    main()
