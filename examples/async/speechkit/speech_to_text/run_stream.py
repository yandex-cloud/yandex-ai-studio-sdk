#!/usr/bin/env python3
"""
This is example is about .run_stream usage, but also is about how to process resulting events stream.
"""

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncAIStudio

SAMPLERATE = 44100


async def get_audio_data(sdk: AsyncAIStudio, request: str) -> bytes:
    """TTS is just a random source of voice data and it is not related to this example in any way."""
    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    tts_result = await tts.run(request)
    return tts_result.data


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

    audio_data = await get_audio_data(sdk, "Hey! How are you doing?")

    stt = sdk.speechkit.speech_to_text(
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
        language_codes='en_EN',
    )

    async for event in stt.run_stream(audio_data):
        channel_tag = event.channel_tag or "NO_CHANNEL"

        ### First approach - is to look for event_type-specific fields:
        if partial := event.partial:
            print(f'[channel {channel_tag}] New partial: {partial.text!r}')

        if final := event.final:
            print(f'[channel {channel_tag}] New final: {final.text!r}')

        if final_refinement := event.final_refinement:
            print(f'[channel {channel_tag}] New final_refinement: {final_refinement.text!r}')

        ### Second approach - is to use match-case, based on event_type:
        match event.event_type:
            case 'final_refinement':
                assert event.final_refinement
                print(f'[channel {channel_tag}] final_refinement via match/case: {event.final_refinement.text!r}')
            case _ :
                print(f'[channel {channel_tag}] Got {event.event_type!r} event')

        ### Third approach is to use helper-property .text:
        if event.text:
            print(f"{event.event_type!r} have a {event.text=}")


if __name__ == '__main__':
    asyncio.run(main())
