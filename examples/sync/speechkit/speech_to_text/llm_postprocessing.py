#!/usr/bin/env python3

"""
This example shows a way to configure llm_post_process (summarize)
and ways to get its results.
"""

from __future__ import annotations

import pprint

import numpy as np
from pydantic import BaseModel, Field

from yandex_ai_studio_sdk import AIStudio

SAMPLERATE = 44100

def get_audio_data(sdk: AIStudio) -> bytes:
    """This function is just a source of two-channel conversation
    for an example purposes.
    """

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    voice_data_first = tts.run('Привет! Как дела?')
    tts = tts.configure(voice='jane')
    voice_data_second = tts.run("Привет-привет! Хорошо! А твои?")

    left = np.frombuffer(voice_data_first.data, dtype=np.int16)
    right = np.frombuffer(voice_data_second.data, dtype=np.int16)
    len_silence = 3 * SAMPLERATE

    len_left = len(left)
    len_right = len(right)

    left_channel = np.concatenate([left, np.zeros(len_right + len_silence, dtype=np.int16)])
    right_channel = np.concatenate([np.zeros(len_left + len_silence, dtype=np.int16), right])

    stereo = np.column_stack((left_channel, right_channel)).flatten()  # type: ignore[attr-defined]

    return stereo.tobytes()


def get_pydantic_model() -> type[BaseModel]:
    class Conversation(BaseModel):
        location: str = Field(description="Name of the place where conversation is taking place")
        topic: str = Field()
        actors: list[str] = Field()

    return Conversation


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
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE, channels=2),
        language_codes='ru_RU',
    )

    stt = stt.configure(
        llm_post_process=stt.LLMPostProcessing('aliceai-llm').with_instruction(
            'Краткое резюме разговора'
        ).with_instruction(
            'Краткое резюме разговора, опиши акторов, ответь в json',
            response_format='json',
        ).with_instruction(
            'Краткое резюме разговора, ответь, используя предоставленную схему',
            # More on the response_format topic you can find at
            # examples/<sync/>/chat/structured_output.py example
            response_format=get_pydantic_model(),
        )
    )

    # First of all, example on how to get analysis results for stream events:
    for event in stt.run_stream(audio_data):
        if llm_post_process_result := event.llm_post_process_result:
            print('New llm post process result:')
            for instruction, result_text in llm_post_process_result.by_instructions.items():
                print(f'>>> {instruction}: {result_text}')

    # And example on how to access analysis result from synchronous call
    result = stt.run(audio_data)
    pprint.pprint(result.llm_post_process_result)

if __name__ == '__main__':
    main()
