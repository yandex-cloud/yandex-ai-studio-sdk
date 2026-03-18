#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncAIStudio

SAMPLERATE = 44100


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
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
        # Classifiers working only with russian language, so in purpose of this
        # example we use russian
        language_codes='ru_RU',
        recognition_classifiers=(
            sdk.speechkit.speech_to_text.RecognitionClassifier.on_utterance('informal_greeting'),
        ),
    )
    stt = stt.configure(
        recognition_classifiers=(
            # you could also use the shortcuts for all of the data structures
            stt.RecognitionClassifier.on_utterance('informal_greeting'),
            stt.RecognitionClassifier.on_utterance(
                stt.RecognitionClassifier.WellKnown.informal_farewell,
            ),
        )
    )
    bistream = stt.create_bistream()

    async def producer():
        async for input_chunk in tts.run_stream('Привет! Как дела?'):
            print(f'>>> Sending {len(input_chunk.data)=} bytes')
            await bistream.write(input_chunk.data)

        await asyncio.sleep(1)

        print('>>> Sending 1 second of silence')
        await bistream.write_silence(1000)

        await asyncio.sleep(1)

        input_chunk = await tts.run('Хорошего вечера, пока!')
        print(f'>>> Sending {len(input_chunk.data)=} bytes')
        await bistream.write(input_chunk.data)

        await bistream.done_writing()

    task = asyncio.create_task(producer())

    async for recognition_result in bistream:
        print(f'<<< got new {recognition_result=}')

    await task


if __name__ == '__main__':
    asyncio.run(main())
