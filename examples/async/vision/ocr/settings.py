#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_ai_studio_sdk import AsyncAIStudio


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    content = (pathlib.Path(__file__).parent / 'example.png').read_bytes()

    # You can pass settings when creating the OCR object
    ocr = sdk.vision.ocr(
        language_codes=['ru', 'en'],
        model='page',
    )

    # And reconfigure at any time — the original object is not mutated
    ocr_handwritten = ocr.configure(model='handwritten')

    result = await ocr.run(content)
    print('=== page model ===')
    for page in result:
        print(f'Page {page.page}: {page.full_text[:80]}')

    result = await ocr_handwritten.run(content)
    print('=== handwritten model ===')
    for page in result:
        print(f'Page {page.page}: {page.full_text[:80]}')

    # mime_type is detected automatically from content magic bytes,
    # but you can also pass it explicitly:
    result = await ocr.run(content, mime_type='image/jpeg')
    print('=== explicit mime_type ===')
    for page in result:
        print(f'Page {page.page}: {page.full_text[:80]}')


if __name__ == '__main__':
    asyncio.run(main())
