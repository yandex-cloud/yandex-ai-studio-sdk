#!/usr/bin/env python3
"""
This example is showing method to work with bidirectional recognition stream,
which is allows to process big inputs in realtime.
"""

from __future__ import annotations

import threading
import time

from yandex_ai_studio_sdk import AIStudio

SAMPLERATE = 44100


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    stt = sdk.speechkit.speech_to_text(
        model='general',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
        language_codes='ru_RU',
    )

    bistream = stt.create_bistream()

    def producer(writer):
        for input_chunk in tts.run_stream('Привет! Как дела?'):
            seconds = len(input_chunk.data) / SAMPLERATE
            print(f'>>> Sending {seconds} seconds of data')

            # here we are hronously writing audio data into bistream
            bistream.write(input_chunk.data)

        time.sleep(1)

        silence = 2
        print(f'>>> Sending {silence} seconds of silence')
        # here we are writing silince to trigger EOU at recognition
        writer.write_silence(1000 * silence)

        time.sleep(1)

        input_chunk = tts.run('Хорошего вечера, пока!')
        seconds = len(input_chunk.data) / SAMPLERATE
        print(f'>>> Sending {seconds} seconds data')
        # new chunk of audio data after a silence
        writer.write(input_chunk.data)

        # we must explicitly tell to stream that we are done
        # to make it release reading iterator
        writer.done_writing()

    # we are creating thread here for writing data into the bistream,
    # but it could be any way around
    input_thread = threading.Thread(
        target=producer,
        kwargs={'writer': bistream},
    )
    input_thread.start()

    try:
        # iterating and processing stream events is nothing different from .run_stream method
        # and this topic have more coverage at run_stream.py example
        for recognition_event in bistream:
            if recognition_event.event_type == 'status_code':
                continue
            print(f'<<< got new {recognition_event=}')
    finally:
        input_thread.join(5)


if __name__ == '__main__':
    main()
