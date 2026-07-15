# pylint: disable=protected-access
from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from yandex_ai_studio_sdk._experimental.audio.out import AsyncAudioOut

np = pytest.importorskip('numpy')

SAMPLERATE = 44100
BLOCKSIZE = 100


@pytest_asyncio.fixture(name='out')
async def out_fixture() -> AsyncAudioOut:
    """AsyncAudioOut with the queue set up manually: no audio device or even
    sounddevice needed — the tests drive the queue and the callback directly."""
    out = AsyncAudioOut(samplerate=SAMPLERATE, blocksize=BLOCKSIZE)
    out._loop = asyncio.get_running_loop()
    out._queue = asyncio.Queue()
    return out


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
