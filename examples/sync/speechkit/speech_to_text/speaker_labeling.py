#!/usr/bin/env python3
"""
This example shows a way to configure classifiers
and ways to get its results.
"""

from __future__ import annotations

import numpy as np

from yandex_ai_studio_sdk import AIStudio

SAMPLERATE = 44100

# pylint: disable=too-many-locals
def get_audio_data(sdk: AIStudio) -> bytes:
    """This function is just a source of two-channel conversation
    for an example purposes.
    """

    dtype = np.int16

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    voice_data_first = tts.run('Привет! Как дела?')
    tts = tts.configure(voice='jane')
    voice_data_second = tts.run("Привет-привет! Хорошо! А твои?")
    tts = tts.configure(voice='kirill')
    voice_data_third = tts.run('И мои хорошо!')

    silence = np.zeros(5 * SAMPLERATE, dtype=dtype)

    first = np.frombuffer(voice_data_first.data, dtype=dtype)
    second = np.frombuffer(voice_data_second.data, dtype=dtype)
    third = np.frombuffer(voice_data_third.data, dtype=dtype)
    data = np.concatenate([first, silence, second, silence, third])

    return data.tobytes()


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

    audio_data = get_audio_data(sdk)

    stt = sdk.speechkit.speech_to_text(
        # audio_format='wav',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
        language_codes='ru_RU',
        speaker_labeling=True,
    )
    # speaker labeling is available only in deferred run
    operation = stt.run_deferred(audio_data)
    result = operation.wait()
    # It is dividing result into few channels:
    for channel in result:
        print(f'[{channel.tag=}] {channel.text}')

    # To make it into conversation, lets make an utterance array
    # and sort it by utterance's timespans
    pairs: list[tuple[str, float, str]] = []
    for channel in result:
        pairs.extend(
            (channel.tag, utterance.timespan.start_time_ms, utterance.text)
            for utterance in channel.utterances
        )
    pairs.sort(key=lambda pair: pair[1])
    for index, start_time_ms, text in pairs:
        print(f'[{start_time_ms}] {index} >>> {text}')


if __name__ == '__main__':
    main()
