#!/usr/bin/env python3

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

    ocr = sdk.vision.ocr(language_codes=['ru'], model='license-plates')

    content = (pathlib.Path(__file__).parent / 'license_plate.jpg').read_bytes()

    result = ocr.run(content)

    for page in result:
        print(f'=== Page {page.page} ===')
        for block in page.blocks:
            for line in block:
                for word in line:
                    print(f'  {word.text}')


if __name__ == '__main__':
    main()
