#!/usr/bin/env python3
"""
This example shows how to use .run_deferred to submit an OCR job and retrieve
the result synchronously via an operation object.

Unlike .run (which blocks until recognition is complete), .run_deferred returns
an operation immediately. You can save the operation ID, poll later, or restore
the operation from its ID if your process restarts.
"""

from __future__ import annotations

import pathlib

from yandex_ai_studio_sdk import AIStudio


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    ocr = sdk.vision.ocr(language_codes=['ru', 'en'], model='page')

    content = (pathlib.Path(__file__).parent / 'example.png').read_bytes()

    # Simple deferred pipeline: submit → wait → print.
    operation = ocr.run_deferred(content)
    result = operation.wait()

    for page in result:
        print(f'=== Page {page.page} ===')
        print(page.full_text)

    # Showcase of operation restore via attach_deferred.
    # If you saved the operation ID (e.g. in a database) and want to retrieve
    # the result later — possibly from a different process — use attach_deferred:
    operation = ocr.run_deferred(content)
    operation_id = operation.id

    restored_operation = ocr.attach_deferred(operation_id)
    result = restored_operation.wait()

    for page in result:
        print(f'=== Page {page.page} ===')
        print(page.full_text)


if __name__ == '__main__':
    main()
