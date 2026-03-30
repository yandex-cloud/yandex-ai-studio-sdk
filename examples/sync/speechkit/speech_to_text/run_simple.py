#!/usr/bin/env python3
"""
Minimalistic example on how to use speech to text without any additional
settings.
"""

from __future__ import annotations

import pprint

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

    request_text = 'Hello! How are you?'
    voice_data = get_voice_data(sdk, request_text)

    stt = sdk.speechkit.speech_to_text(
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
        # explicit language_code is way better for non-russian languages
        language_codes='en_EN',
    )

    result = stt.run(voice_data)

    print(f"{request_text=}")
    print(f"{result.text=}")

    # result object have a rich structure for any kind of investingations
    pprint.pprint(result)


if __name__ == '__main__':
    main()
