#!/usr/bin/env python3
"""
This example shows how to work with deferred operations, returned by .run_deferred method.

It shows nothing special about Speech to Text itself.
"""

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncAIStudio

SAMPLERATE = 44100


async def get_voice_data(sdk: AsyncAIStudio) -> bytes:
    """TTS is just a random source of voice data and it is not related to this example in any way."""

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    # * 15 for proper length to make model work more than 1 second
    # for this example needs
    tts_result = await tts.run('Hello! How are you? How are the weather? ' * 15)
    return tts_result.data


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

    voice_data = await get_voice_data(sdk)
    stt = sdk.speechkit.speech_to_text(
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
        language_codes='en_EN',
        # NB: The deferred-general model is a special model
        # that makes deferred runs even more deferred, at a lower price.
        # You can still use the default or any other model for your deferred runs.
        # More at https://aistudio.yandex.ru/docs/speechkit/stt/transcribation.html#modes
        model='deferred-general'
    )

    # most simple deferred pipeline:
    operation = await stt.run_deferred(voice_data)
    result = await operation.wait()
    await result.delete()

    # showcase on operation restore
    operation = await stt.run_deferred(voice_data)
    try:
        result = await operation.wait(poll_timeout=1, poll_interval=0.01)
    except TimeoutError:
        print('operation wait timeout')

        # let's assume you created the operation, saved its id in some DB
        # and want to restore operation object
        restored_operation = await stt.attach_deferred(operation.id)
        result = await restored_operation.wait(poll_timeout=100)

    # also you can get result at any time
    result2 = await sdk.speechkit.speech_to_text.get_recognition_result(operation.id)
    assert result == result2
    print(f"{result.text=}")
    # and not forget to clean it
    await result.delete()


if __name__ == '__main__':
    asyncio.run(main())
