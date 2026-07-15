# pylint: disable=protected-access
from __future__ import annotations

import asyncio
import importlib
import sys
from typing import TYPE_CHECKING
from collections.abc import AsyncIterator
from unittest import mock

import pytest
import pytest_asyncio

np = pytest.importorskip('numpy')

if TYPE_CHECKING:
    from yandex_ai_studio_sdk._experimental.audio.out import AsyncAudioOut

OUT_MODULE = 'yandex_ai_studio_sdk._experimental.audio.out'

SAMPLERATE = 44100
BLOCKSIZE = 100


@pytest_asyncio.fixture(name='out')
async def out_fixture() -> AsyncIterator[AsyncAudioOut]:
    """AsyncAudioOut with mocked sounddevice and a manually set up queue.

    sounddevice needs the PortAudio system library even at import time and CI
    has no audio devices; the tests below drive the queue and the callback
    directly. The mock is scoped to the fixture and the cached module is
    dropped afterwards, so nothing leaks into other test files.
    """
    sys.modules.pop(OUT_MODULE, None)
    with mock.patch.dict(sys.modules, {'sounddevice': mock.MagicMock()}):
        out_module = importlib.import_module(OUT_MODULE)
        audio_out = out_module.AsyncAudioOut(samplerate=SAMPLERATE, blocksize=BLOCKSIZE)
        audio_out._loop = asyncio.get_running_loop()
        audio_out._queue = asyncio.Queue()
        yield audio_out
    sys.modules.pop(OUT_MODULE, None)


def drain_one_block(out: AsyncAudioOut) -> None:
    """Simulate the PortAudio callback consuming one block from the queue."""
    outdata = np.zeros((BLOCKSIZE, 1), dtype='int16')
    out._callback(outdata, BLOCKSIZE, None, None)


@pytest.mark.asyncio
async def test_played_ms_counts_only_played_payload(out):
    # 3 blocks of 100 samples; 100 samples at 44100 Hz int16 = 200 bytes
    await out.write(b'\x01\x02' * 300)
    assert out.written_ms == pytest.approx(300 / SAMPLERATE * 1000)
    assert out.played_ms == 0

    drain_one_block(out)
    assert out.played_ms == pytest.approx(100 / SAMPLERATE * 1000)

    drain_one_block(out)
    drain_one_block(out)
    assert out.played_ms == pytest.approx(out.written_ms)

    # queue is empty: callback outputs silence, played_ms must not grow
    drain_one_block(out)
    assert out.played_ms == pytest.approx(out.written_ms)


@pytest.mark.asyncio
async def test_padding_silence_is_not_counted(out):
    # 150 samples: one full block and one half-filled block padded with silence
    await out.write(b'\x01\x02' * 150)

    drain_one_block(out)
    drain_one_block(out)
    assert out.played_ms == pytest.approx(150 / SAMPLERATE * 1000)


@pytest.mark.asyncio
async def test_clear_returns_played_and_resets(out):
    await out.write(b'\x01\x02' * 300)
    drain_one_block(out)

    played = await out.clear()
    assert played == pytest.approx(100 / SAMPLERATE * 1000)
    assert out.played_ms == 0
    assert out.written_ms == 0
    assert out.queue_size == 0

    # writing after clear starts a fresh count
    await out.write(b'\x01\x02' * 100)
    drain_one_block(out)
    assert out.played_ms == pytest.approx(100 / SAMPLERATE * 1000)
