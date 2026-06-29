from __future__ import annotations

import pathlib

import pytest

from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._vision.ocr.utils import detect_mime_type
from yandex_ai_studio_sdk.exceptions import AIStudioConfigurationError


def test_detect_mime_type_jpeg() -> None:
    assert detect_mime_type(b'\xff\xd8\xff\xe0' + b'\x00' * 10) == 'image/jpeg'


def test_detect_mime_type_png() -> None:
    assert detect_mime_type(b'\x89PNG\r\n\x1a\n' + b'\x00' * 10) == 'image/png'


def test_detect_mime_type_pdf() -> None:
    assert detect_mime_type(b'%PDF-1.4' + b'\x00' * 10) == 'application/pdf'


def test_detect_mime_type_unknown_raises() -> None:
    with pytest.raises(AIStudioConfigurationError, match='unable to detect MIME type'):
        detect_mime_type(b'\x00\x01\x02\x03')


def test_detect_mime_type_empty_raises() -> None:
    with pytest.raises(AIStudioConfigurationError, match='unable to detect MIME type'):
        detect_mime_type(b'')


@pytest.fixture(name='image')
def image_fixture() -> pathlib.Path:
    return pathlib.Path(__file__).parent / 'image.png'


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_ocr_simple_run(async_sdk: AsyncAIStudio, image: pathlib.Path) -> None:
    ocr = async_sdk.vision.ocr(language_codes=['ru', 'en'])
    result = await ocr.run(image.read_bytes())
    assert len(result) >= 1
    page = result[0]
    assert page.full_text
    assert len(page.blocks) >= 1
    for block in page.blocks:
        assert len(block) >= 1
        for line in block:
            assert line.text
            assert len(line) >= 1


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_ocr_run_deferred(async_sdk: AsyncAIStudio, image: pathlib.Path) -> None:
    ocr = async_sdk.vision.ocr(language_codes=['ru', 'en'])
    operation = await ocr.run_deferred(image.read_bytes())
    assert operation.id
    result = await operation.wait()
    assert len(result) >= 1
    assert result[0].full_text


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_ocr_attach_deferred(async_sdk: AsyncAIStudio, image: pathlib.Path) -> None:
    ocr = async_sdk.vision.ocr(language_codes=['ru', 'en'])
    operation = await ocr.run_deferred(image.read_bytes())
    operation_id = operation.id

    restored = await ocr.attach_deferred(operation_id)
    result = await restored.wait()
    assert len(result) >= 1
    assert result[0].full_text


def test_ocr_configure(async_sdk: AsyncAIStudio) -> None:
    # pylint: disable=protected-access
    ocr = async_sdk.vision.ocr(language_codes='ru', model='page')
    assert ocr._config.language_codes == ('ru',)
    assert ocr._config.model == 'page'

    ocr2 = ocr.configure(language_codes=['ru', 'en'], model='handwritten')
    assert ocr2._config.language_codes == ('ru', 'en')
    assert ocr2._config.model == 'handwritten'

    # original unchanged
    assert ocr._config.language_codes == ('ru',)


def test_ocr_configure_none(async_sdk: AsyncAIStudio) -> None:
    # pylint: disable=protected-access
    ocr = async_sdk.vision.ocr()
    assert ocr._config.language_codes is None
    assert ocr._config.model is None


@pytest.fixture(name='table_image')
def table_image_fixture() -> pathlib.Path:
    return pathlib.Path(__file__).parent / 'table.jpg'


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_ocr_table_result(async_sdk: AsyncAIStudio, table_image: pathlib.Path) -> None:
    ocr = async_sdk.vision.ocr(language_codes=['ru', 'en'], model='table')
    result = await ocr.run(table_image.read_bytes())

    assert len(result) >= 1
    page = result[0]

    assert len(page.tables) >= 1
    table = page.tables[0]

    assert table.row_count >= 1
    assert table.column_count >= 1
    assert len(table) == len(table.cells)
    assert len(table) >= 1

    for cell in table:
        assert cell.row_index >= 0
        assert cell.column_index >= 0
        assert cell.row_span >= 1
        assert cell.column_span >= 1
        assert len(cell.bounding_box) == 4

    # All cells fit within the declared grid dimensions
    for cell in table:
        assert cell.row_index + cell.row_span <= table.row_count
        assert cell.column_index + cell.column_span <= table.column_count
