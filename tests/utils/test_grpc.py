# @author Vladislav-Kor <corchagin.vlad2005@yandex.ru>
# Date: 06.11.2026
# Time: 06:48
from __future__ import annotations

from yandex_ai_studio_sdk._utils.grpc import StreamStreamCallResponseIterator, UnaryStreamCallResponseIterator


class FakeCall:
    def __init__(self) -> None:
        self.callbacks: list = []

    def add_done_callback(self, callback) -> None:
        self.callbacks.append(callback)


async def no_responses():
    for item in ():
        yield item


def test_add_done_callback_delegates_to_underlying_call() -> None:
    for klass in (UnaryStreamCallResponseIterator, StreamStreamCallResponseIterator):
        call = FakeCall()
        stream = klass(call, no_responses())  # type: ignore[arg-type]

        def callback(_) -> None:
            pass

        stream.add_done_callback(callback)

        assert call.callbacks == [callback]


def test_add_done_callback_without_underlying_call_fires_immediately() -> None:
    stream = UnaryStreamCallResponseIterator(None, no_responses())  # type: ignore[arg-type]
    called_with: list = []

    stream.add_done_callback(called_with.append)

    assert called_with == [stream]
    assert stream.done()
