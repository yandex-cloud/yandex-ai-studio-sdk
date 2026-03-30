#!/usr/bin/env python3
"""
This example shows how possibility to pass an s3 with data instead of bytes into .run_deferred
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import boto3
import botocore.exceptions

from yandex_ai_studio_sdk import AIStudio

SAMPLERATE = 44100


def get_voice_data(sdk: AIStudio) -> bytes:
    """TTS is just a random source of voice data and it is not related to this example in any way."""

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
    )
    # * 15 for proper length to make model work more than 1 second
    # for this example needs
    tts_result = tts.run('Hello! How are you? How are the weather? ' * 15)
    return tts_result.data


@contextmanager
def get_s3_url(voice_data: bytes) -> Iterator[str]:
    """
    We are assuming you have setup your credentials
    for usage via boto3 with the instruction
    https://yandex.cloud/ru/docs/storage/tools/boto
    """

    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

    bucket_name = 'yandex-ai-studio-sdk-examples-speechkit-run-deferred-s3'
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f'bucket {bucket_name} is already exists')
    except botocore.exceptions.ClientError:
        s3.create_bucket(Bucket=bucket_name)
        print(f'bucket {bucket_name} created')

    key = str(uuid.uuid4())
    s3.put_object(Bucket=bucket_name, Key=key, Body=voice_data)
    presigned_url: str = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
        ExpiresIn=100,
    )

    try:
        yield presigned_url
    finally:
        s3r = boto3.resource('s3')
        bucket = s3r.Bucket(bucket_name)
        bucket.objects.all().delete()
        s3.delete_bucket(Bucket=bucket_name)


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

    voice_data = get_voice_data(sdk)
    stt = sdk.speechkit.speech_to_text(
        audio_format=sdk.speechkit.AudioFormat.PCM16(SAMPLERATE),
        language_codes='en_EN',
    )
    # in this example we are generating and uploading data by ourselves
    # to s3 for example purposes
    with get_s3_url(voice_data) as url:
        # Main difference from run_deferred - we are using string input
        # instead of bytes
        operation = stt.run_deferred(url)
        result = operation.wait()
        print(result.text)
        result.delete()


if __name__ == '__main__':
    main()
