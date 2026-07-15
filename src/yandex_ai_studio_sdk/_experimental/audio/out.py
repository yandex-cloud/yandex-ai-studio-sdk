#!/usr/bin/env python3
"""
Experimental module for async audio data consumer;

To use it: ``pip install sounddevice numpy``
At Ubuntu also: ``sudo apt install libportaudio2``
At Windows and MacOS PortAudio will be installed automagically.

AsyncAudioOut tracks playback progress: ``played_ms`` is the duration of audio
actually handed to the output device (padding silence excluded), ``written_ms``
is the duration written so far. ``clear()`` drops the queued tail and returns
the played duration. This makes honest barge-in handling possible in realtime
voice agents: on interruption the caller knows exactly how much of the response
the user heard (e.g. for ``conversation.item.truncate`` in the Realtime API).

NB: AsyncAudioOut is not threadsafe!
"""

from __future__ import annotations

import asyncio
import types
from typing import Any

import numpy as np
from typing_extensions import Self

try:
    import sounddevice as sd
except (ImportError, OSError):  # sounddevice also needs the PortAudio system library
    # the module stays importable without sounddevice: it is only required
    # to actually open the output stream
    sd = None  # type: ignore[assignment]


OUT_RATE = 44100
OUT_BLOCK = int(OUT_RATE * 0.02)

DTYPE = 'int16'
QUEUE_ITEM_SIZE = OUT_BLOCK * 2  # size of int16 in queue
MAX_QUEUE_SIZE_BYTES = 500 * 1024 ** 2  # 500 MB
MAX_QUEUE_SIZE = MAX_QUEUE_SIZE_BYTES // QUEUE_ITEM_SIZE


class AsyncAudioOut:
    def __init__(
        self,
        *,
        device_id: int | None = None,
        samplerate: int = OUT_RATE,
        blocksize: int = OUT_BLOCK,
    ):
        self._device_id = device_id
        self._samplerate = samplerate
        self._blocksize = blocksize

        self._stopped = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[tuple[np.ndarray, int] | None] | None = None
        self._stream: sd.OutputStream | None = None
        self._write_lock = asyncio.Lock()
        self._start_lock = asyncio.Lock()
        # payload bytes only, padding silence excluded
        self._played_bytes = 0
        self._written_bytes = 0

    @property
    def queue_size(self) -> int:
        assert self._queue
        return self._queue.qsize()

    @property
    def played_ms(self) -> float:
        """Duration of audio actually handed to the output device since open/last clear()."""
        return self._bytes_to_ms(self._played_bytes)

    @property
    def written_ms(self) -> float:
        """Duration of audio written via write() since open/last clear()."""
        return self._bytes_to_ms(self._written_bytes)

    def _bytes_to_ms(self, size: int) -> float:
        return size / 2 / self._samplerate * 1000

    async def __aenter__(self) -> Self:
        if sd is None:
            raise RuntimeError(
                'sounddevice is not available; see the module docstring for installation notes'
            )
        async with self._start_lock:
            if self._loop:
                raise RuntimeError('cannot use AsyncAudioOut simultaneously')

            self._loop = asyncio.get_running_loop()
            self._queue = asyncio.Queue(MAX_QUEUE_SIZE)
            self._played_bytes = 0
            self._written_bytes = 0
            self._stream = sd.OutputStream(
                samplerate=self._samplerate,
                channels=1,
                dtype=DTYPE,
                blocksize=self._blocksize,
                callback=self._callback
            )
            self._stopped.clear()
            await self._loop.run_in_executor(None, self._stream.start)
            return self

    # pylint: disable=unused-argument
    def _callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time: Any,
        status: sd.CallbackFlags,
    ) -> None:
        # NB: callback is called in separate thread
        # and self._queue could be nullified in __aexit__
        queue = self._queue
        if not queue:
            outdata.fill(0)
            return

        assert self._loop
        try:
            item = queue.get_nowait()
            if item is None:
                self._loop.call_soon_threadsafe(self._stopped.set)
                return

            chunk, payload_size = item
            outdata[:] = chunk
            self._played_bytes += payload_size
        except asyncio.QueueEmpty:
            outdata.fill(0)
        return

    async def clear(self) -> float:
        """Drop queued audio and return how many ms were actually played.

        Intended for barge-in: the return value is the exact duration the user
        heard before the interruption.
        """
        played = self.played_ms
        self._queue = asyncio.Queue()
        self._played_bytes = 0
        self._written_bytes = 0
        return played

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None
    ) -> bool | None:
        queue = self._queue
        async with self._start_lock:
            if queue:
                await queue.put(None)
            try:
                await self._stopped.wait()
            finally:
                try:
                    if self._stream and self._loop and self._stream.active:
                        await self._loop.run_in_executor(None, self._stream.stop)
                except:
                    if self._stream and self._loop and self._stream.active:
                        await self._loop.run_in_executor(None, self._stream.abort)
                    raise
                finally:
                    self._queue = None
                    self._loop = None
                    self._stream = None

        return None

    async def write(self, pcm_16: bytes) -> None:
        # NB: callback is called in separate thread
        # and self._queue could be nullified in __aexit__
        queue = self._queue
        if not queue:
            raise RuntimeError('trying to write into closed AsyncAudioOut')

        chunk_size = 2 * self._blocksize
        payload_size = len(pcm_16)

        async with self._write_lock:
            for i in range(0, payload_size, chunk_size):
                end = min((payload_size, i + chunk_size))
                chunk = pcm_16[i:end].ljust(chunk_size, b'\x00')
                array = np.frombuffer(chunk, dtype=DTYPE)  # type: ignore[arg-type]
                await queue.put((array.reshape(-1, 1), end - i))
            self._written_bytes += payload_size


async def main() -> None:
    # pylint: disable=import-outside-toplevel
    try:
        from .microphone import AsyncMicrophone
        from .utils import choose_audio_device
    except ImportError:
        from microphone import AsyncMicrophone  # type: ignore[no-redef,import-not-found,attr-defined]
        from utils import choose_audio_device  # type: ignore[no-redef,import-not-found,attr-defined]

    mic_id = choose_audio_device('in')
    out_id = choose_audio_device('out')

    mic = AsyncMicrophone(device_id=mic_id, samplerate=OUT_RATE, blocksize=OUT_BLOCK)
    i = 0
    async with AsyncAudioOut(device_id=out_id) as out:
        async for payload in mic:
            i += 1
            if i % 100 == 0:
                print(f"Microphone queue: {mic.queue_size}; output queue: {out.queue_size}")
            await out.write(payload)


if __name__ == '__main__':
    asyncio.run(main())
