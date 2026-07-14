# pylint: disable=protected-access
from __future__ import annotations

import asyncio

import pytest

np = pytest.importorskip('numpy')
pytest.importorskip('sounddevice')

from yandex_ai_studio_sdk._experimental.audio.out import AsyncAudioOut  # noqa: E402


def make_out(samplerate: int = 44100, blocksize: int = 100) -> AsyncAudioOut:
    """AsyncAudioOut with the queue set up manually: no real audio device needed."""
    out = AsyncAudioOut(samplerate=samplerate, blocksize=blocksize)
    out._loop = asyncio.get_running_loop()
    out._queue = asyncio.Queue()
    return out


def drain_one_block(out: AsyncAudioOut, blocksize: int = 100) -> None:
    """Simulate the PortAudio callback consuming one block from the queue."""
    outdata = np.zeros((blocksize, 1), dtype='int16')
    out._callback(outdata, blocksize, None, None)


@pytest.mark.asyncio
async def test_played_ms_counts_only_played_payload():
    out = make_out()
    # 3 blocks of 100 samples; 100 samples at 44100 Hz int16 = 200 bytes
    await out.write(b'\x01\x02' * 300)
    assert out.written_ms == pytest.approx(300 / 44100 * 1000)
    assert out.played_ms == 0

    drain_one_block(out)
    assert out.played_ms == pytest.approx(100 / 44100 * 1000)

    drain_one_block(out)
    drain_one_block(out)
    assert out.played_ms == pytest.approx(out.written_ms)

    # queue is empty: callback outputs silence, played_ms must not grow
    drain_one_block(out)
    assert out.played_ms == pytest.approx(out.written_ms)


@pytest.mark.asyncio
async def test_padding_silence_is_not_counted():
    out = make_out()
    # 150 samples: one full block and one half-filled block padded with silence
    await out.write(b'\x01\x02' * 150)

    drain_one_block(out)
    drain_one_block(out)
    assert out.played_ms == pytest.approx(150 / 44100 * 1000)


@pytest.mark.asyncio
async def test_clear_returns_played_and_resets():
    out = make_out()
    await out.write(b'\x01\x02' * 300)
    drain_one_block(out)

    played = await out.clear()
    assert played == pytest.approx(100 / 44100 * 1000)
    assert out.played_ms == 0
    assert out.written_ms == 0
    assert out.queue_size == 0

    # writing after clear starts a fresh count
    await out.write(b'\x01\x02' * 100)
    drain_one_block(out)
    assert out.played_ms == pytest.approx(100 / 44100 * 1000)
