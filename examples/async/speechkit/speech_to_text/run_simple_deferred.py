#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncAIStudio

SAMPLERATE = 44100


async def get_voice_data(sdk: AsyncAIStudio) -> bytes:
    """TTS here is just random source of voice data
    and it's not related in any way to this example topic.
    """

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    # * 15 for proper length to make model work more than 1 second
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
    )

    # most simple deferred pipeline:
    operation = await stt.run_deferred(voice_data.data)
    result = await operation.wait()
    print(result)
    await result.delete()

    # showcase on operation restore
    operation = await stt.run_deferred(voice_data.data)
    try:
        # NB: we are not assigning this call to a variable
        # to showcase result fetching later
        await operation.wait(poll_timeout=1, poll_interval=0.01)
    except TimeoutError:
        print('operation wait timeout')

        # let's assume you created the operation, saved its id
        # and want to restore operation object
        restored_operation = await stt.attach_deferred(operation.id)
        await restored_operation.wait(poll_timeout=100)

    # also you can get result at any time
    result = sdk.speechkit.speech_to_text.get_recognition_result(operation.id)
    # and not forget to clean it
    await result.delete()


if __name__ == '__main__':
    asyncio.run(main())
