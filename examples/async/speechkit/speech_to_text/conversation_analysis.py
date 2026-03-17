#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pprint

import numpy as np

from yandex_ai_studio_sdk import AsyncAIStudio

SAMPLERATE = 44100

# pylint: disable=too-many-locals
async def get_audio_data(sdk: AsyncAIStudio) -> bytes:
    """This function is just a source of two-channel conversation
    for an example purposes.
    """

    dtype = np.int16

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    voice_data_first = await tts.run('Привет! Как дела?')
    voice_data_third = await tts.run('Все, нет времени, пока')
    tts = tts.configure(voice='jane')
    voice_data_second = await tts.run("Привет-привет! Хорошо! А твои?")

    left = np.frombuffer(voice_data_first.data, dtype=dtype)
    left2 = np.frombuffer(voice_data_third.data, dtype=dtype)
    right = np.frombuffer(voice_data_second.data, dtype=dtype)
    len_silence = 3 * SAMPLERATE

    len_left = len(left)
    len_right = len(right)

    left_channel = np.concatenate([
        # left utterance
        left,
        # 3s silence + half of the right utterance
        np.zeros(len_silence + int(len_right / 2), dtype=dtype),
        # this utterance should start at the middle of right utterance
        left2,
    ])
    right_channel = np.concatenate([
        # all left utterance + 3s silence
        np.zeros(len_left + len_silence, dtype=dtype),
        # right utterance
        right,
    ])

    # Here i'm adding zeros to right channel
    if len(right_channel) < len(left_channel):
        right_channel = np.concatenate([
            right_channel,
            np.zeros(len(left_channel) - len(right_channel), dtype=dtype)
        ])
    else:
        # right channel is really shouldn't be shorter than left, but what if
        right_channel = right_channel[:len(left_channel)]

    # combining channels
    stereo = np.column_stack((left_channel, right_channel)).flatten() # type: ignore[attr-defined]

    return stereo.tobytes()


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

    audio_data = await get_audio_data(sdk)

    stt = sdk.speechkit.speech_to_text(
        # audio_format='wav',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE, channels=2),
        language_codes='ru_RU',
    )

    stt = stt.configure(
        speech_analysis=stt.SpeechAnalysis(
            speaker_analysis=True,
            conversation_analysis=True,
            descriptive_statistics_quantiles=[0.1, 0.5, 0.9],
        ),
    )

    async for event in stt.run_stream(audio_data):
        if final := event.final:
            print(f'[channel {event.channel_tag}] New final: {final.text!r}')

        if speaker_analysis := event.speaker_analysis:
            print(f'[channel {event.channel_tag}] New speaker analysis:')
            pprint.pprint(speaker_analysis)

        if conversation_analysis := event.conversation_analysis:
            print('New conversation analysis:')
            pprint.pprint(conversation_analysis)


if __name__ == '__main__':
    asyncio.run(main())
