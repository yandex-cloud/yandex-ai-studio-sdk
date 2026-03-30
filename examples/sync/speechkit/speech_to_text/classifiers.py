#!/usr/bin/env python3
"""
This example shows a way to configure classifiers
and ways to get its results.
"""

from __future__ import annotations

import pprint

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
    voice_data_third = tts.run('Все, нет времени, пока')
    tts = tts.configure(voice='jane')
    voice_data_second = tts.run("Привет-привет! Хорошо! А твои?")

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
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE, channels=2),
        language_codes='ru_RU',
        recognition_classifiers=(
            sdk.speechkit.speech_to_text.RecognitionClassifier.on_utterance('informal_greeting'),
        ),
    )
    stt = stt.configure(
        recognition_classifiers=(
            # you could also use the shortcuts for all of the data structures
            stt.RecognitionClassifier.on_utterance('informal_greeting'),
            stt.RecognitionClassifier.on_partial(
                stt.RecognitionClassifier.WellKnown.informal_farewell,
            ),
            stt.RecognitionClassifier.on_final('gender'),
            stt.RecognitionClassifier('formal_farewell', ['on_partial', 'on_final'])
        )
    )

    # First of all, example on how to get analysis results for stream events:
    for event in stt.run_stream(audio_data):
        if classifier_update := event.classifier_update:
            for label, value in classifier_update.labels.items():
                if value > 0.3:
                    print(
                        f'[channel {event.channel_tag}] '
                        f'Classifier {classifier_update.name} triggered with label {label} and value {value} '
                        f'for the {classifier_update.window_type.name} '
                        f'on words {classifier_update.highlights}'
                    )

    # And example on how to access analysis result from synchronous call
    result = stt.run(audio_data)
    for channel in result:
        for utterance in channel:
            # here is only on_utterance classifier results
            for classifier_name, classifier_result in utterance.classifiers.items():
                pprint.pprint((classifier_name, classifier_result))

            for classifier_final_result in utterance.final_classifiers:
                pprint.pprint(classifier_final_result)


if __name__ == '__main__':
    main()
