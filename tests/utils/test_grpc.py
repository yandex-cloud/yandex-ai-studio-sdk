# @author Vladislav-Kor <korindestris@gmail.com>
# Date: 06.11.2026
# Time: 06:48
"""Tests for the stream call wrappers in yandex_ai_studio_sdk._utils.grpc (see #236)."""
from __future__ import annotations

from yandex_ai_studio_sdk._utils.grpc import StreamStreamCallResponseIterator, UnaryStreamCallResponseIterator


class FakeCall:
    """Stands in for a grpc.aio call and records registered done callbacks."""

    def __init__(self) -> None:
        self.callbacks: list = []

    def add_done_callback(self, callback) -> None:
        self.callbacks.append(callback)


async def no_responses():
    """Response iterator required by the wrappers; these tests never iterate it."""
    for item in ():
        yield item


def test_add_done_callback_delegates_to_underlying_call() -> None:
    # Both wrappers share the mixin, so both must hand the callback over instead of raising.
    for klass in (UnaryStreamCallResponseIterator, StreamStreamCallResponseIterator):
        call = FakeCall()
        stream = klass(call, no_responses())  # type: ignore[arg-type]

        def callback(_) -> None:
            pass

        stream.add_done_callback(callback)

        assert call.callbacks == [callback]


def test_add_done_callback_without_underlying_call_fires_immediately() -> None:
    # The retry interceptor creates the wrapper before the first attempt, with no call yet.
    # Such a wrapper reports done(), so a callback must not be lost.
    stream = UnaryStreamCallResponseIterator(None, no_responses())  # type: ignore[arg-type]
    called_with: list = []

    stream.add_done_callback(called_with.append)

    assert called_with == [stream]
    assert stream.done()
