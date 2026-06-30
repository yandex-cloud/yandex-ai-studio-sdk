#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib
import pprint

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

    ocr = sdk.vision.ocr(language_codes=['ru', 'en'], model='page')

    content = (pathlib.Path(__file__).parent / 'example.png').read_bytes()

    result = await ocr.run(content)

    # Print recognized text for each page
    for page in result:
        print(f'=== Page {page.page} ===')
        print(page.full_text)

    # Pretty-print the full result object to inspect the complete structure:
    # TextAnnotation -> blocks -> lines -> words, bounding polygons, entities, etc.
    print('=== Full result structure ===')
    pprint.pprint(result[0])

    # Recognize the same image with the markdown model to get Markdown-formatted output
    ocr_md = ocr.configure(model='markdown')
    result_md = await ocr_md.run(content)

    print('=== Markdown output ===')
    for page in result_md:
        print(f'--- Page {page.page} ---')
        print(page.markdown)


if __name__ == '__main__':
    asyncio.run(main())
