#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._vision.ocr.text_annotation import Table


def _render_table(table: Table, max_cell_width: int = 30) -> str:
    rows = table.row_count
    cols = table.column_count

    grid: list[list[str]] = [['' for _ in range(cols)] for _ in range(rows)]
    for cell in table:
        text = cell.text.replace('\n', ' ')
        if len(text) > max_cell_width:
            text = text[:max_cell_width - 1] + '…'

        for r in range(cell.row_index, cell.row_index + cell.row_span):
            for c in range(cell.column_index, cell.column_index + cell.column_span):
                grid[r][c] = text if (r == cell.row_index and c == cell.column_index) else '↑'

    col_widths = [
        max(len(grid[r][c]) for r in range(rows))
        for c in range(cols)
    ]

    def separator() -> str:
        return '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'

    def row_line(r: int) -> str:
        cells = ' | '.join(grid[r][c].ljust(col_widths[c]) for c in range(cols))
        return f'| {cells} |'

    lines = [separator()]
    for r in range(rows):
        lines.append(row_line(r))
        lines.append(separator())

    return '\n'.join(lines)


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    ocr = sdk.vision.ocr(language_codes=['ru', 'en'], model='table')

    content = (pathlib.Path(__file__).parent / 'table.jpg').read_bytes()

    # Result object have a rich structure but we will focus on .tables field in this example
    result = await ocr.run(content)

    # We are recognizing .jpg file, but in case of PDF there could be more than one page in result.
    for page in result:
        for i, table in enumerate(page.tables):
            print(f'=== Page {page.page}, Table {i} ({table.row_count}x{table.column_count}) ===')
            print(_render_table(table))


if __name__ == '__main__':
    asyncio.run(main())
