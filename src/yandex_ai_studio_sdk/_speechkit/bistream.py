# pylint: disable=no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

import abc
import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator
from typing import TYPE_CHECKING, Generic, TypeVar, cast

import grpc.aio
from yandex.cloud.ai.stt.v3.stt_pb2 import StreamingRequest, StreamingResponse
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import RecognizerStub
from yandex.cloud.ai.tts.v3.tts_pb2 import StreamSynthesisRequest, StreamSynthesisResponse
from yandex.cloud.ai.tts.v3.tts_service_pb2_grpc import SynthesizerStub
from yandex_ai_studio_sdk._client import AsyncCloudClient
from yandex_ai_studio_sdk._types.model_config import ConfigTypeT
from yandex_ai_studio_sdk._types.proto import SDKType
from yandex_ai_studio_sdk._types.request import RequestDetails
from yandex_ai_studio_sdk._types.result import ProtoModelResultTypeT
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync, run_sync_generator

if TYPE_CHECKING:
    # because grpc have a very funny type stubs which are not 100% synced with grpc itself
    EOFType = grpc.aio._EOFType
    EOF = EOFType()
else:
    EOF = grpc.aio.EOF
    EOFType = type(EOF)


RequestTypeT = TypeVar('RequestTypeT', StreamingRequest, StreamSynthesisRequest)
ResponseTypeT = TypeVar('ResponseTypeT', StreamingResponse, StreamSynthesisResponse)
StubTypeT = TypeVar('StubTypeT', SynthesizerStub, RecognizerStub)
InputTypeT = TypeVar('InputTypeT', str, bytes)



class BaseBidirectionalStream(
    abc.ABC,
    Generic[
        ConfigTypeT,
        ProtoModelResultTypeT,
        RequestTypeT,
        ResponseTypeT,
        StubTypeT,
        InputTypeT
    ]
):
    _stub_class: type[StubTypeT]
    _result_class: type[ProtoModelResultTypeT]

    def __init__(
        self,
        *,
        sdk: SDKType,
        config: ConfigTypeT,
        timeout: float,
    ):
        self._sdk = sdk
        self._config = config
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._done_writing_flag = False
        self._done_writing_lock = asyncio.Lock()

        self.__call: grpc.aio.StreamStreamCall | None = None

    @abc.abstractmethod
    async def _create_call(self, timeout: float) -> grpc.aio.StreamStreamCall:
        pass

    async def _get_call(self) -> grpc.aio.StreamStreamCall:
        if self.__call is not None:
            return self.__call

        async with self._lock:
            if self.__call is None:
                self.__call = await self._create_call(timeout=self._timeout)

                options = self._create_stream_options()
                with self._client.with_sdk_error(self._stub_class):
                    await self.__call.write(options)

        return self.__call

    @abc.abstractmethod
    def _create_stream_options(self) -> RequestTypeT:
        pass

    @property
    def _client(self) -> AsyncCloudClient:
        return self._sdk._client

    @abc.abstractmethod
    def _create_request(self, input: InputTypeT) -> RequestTypeT:
        pass

    async def _write_request(self, request: RequestTypeT) -> None:
        """Write a input to be synthesized"""
        async with self._done_writing_lock:
            if self._done_writing_flag:
                raise RuntimeError(
                    f"stream {self.__class__.__name__} is closed for writing new inputs "
                    "after calling .done_writing()"
                )

            call = await self._get_call()

            with self._client.with_sdk_error(self._stub_class):
                await call.write(request)

    async def _write(self, input: InputTypeT) -> None:
        """Send given input into the stream."""

        request = self._create_request(input)
        await self._write_request(request)

    async def _read(self) -> ProtoModelResultTypeT | None:
        """Read chunk of synthesized result.

        Returns ``None`` in case of closed stream.
        """

        call = await self._get_call()

        with self._client.with_sdk_error(self._stub_class):
            response: ResponseTypeT | EOFType = await call.read()
            if response == EOF:
                return None

            return self._result_class._from_proto(
                proto=cast(ProtoModelResultTypeT, response),
                sdk=self._sdk,
                ctx=RequestDetails(model_config=self._config, timeout=self._timeout)
            )

    async def _gen(self) -> AsyncGenerator[ProtoModelResultTypeT]:
        """Returns generator over all synthesized result parts."""

        try:
            chunk = await self._read()
            while chunk is not None:
                yield chunk
                chunk = await self._read()
        except:
            await self._release()
            raise

    async def _done_writing(self) -> None:
        """Close the stream to tell to a server you done writing.

        Closing the stream will allow any iteration over this stream to exit.

        It is very important to close the stream to properly release resources.
        """

        async with self._done_writing_lock:
            call = await self._get_call()
            self._done_writing_flag = True
            with self._client.with_sdk_error(self._stub_class):
                await call.done_writing()

    async def _release(self) -> None:
        try:
            await self._done_writing()
        finally:
            if self.__call:
                self.__call.cancel()


class AsyncBidirectionalStreamMixin(
    Generic[
        ConfigTypeT,
        ProtoModelResultTypeT,
        RequestTypeT,
        ResponseTypeT,
        StubTypeT,
        InputTypeT
    ],
    BaseBidirectionalStream[
        ConfigTypeT,
        ProtoModelResultTypeT,
        RequestTypeT,
        ResponseTypeT,
        StubTypeT,
        InputTypeT

    ],
    AsyncIterator[ProtoModelResultTypeT]
):
    @doc_from(BaseBidirectionalStream._write)
    async def write(self, input: InputTypeT) -> None:
        await self._write(input)

    @doc_from(BaseBidirectionalStream._read)
    async def read(self) -> ProtoModelResultTypeT | None:
        return await self._read()

    async def __anext__(self) -> ProtoModelResultTypeT:
        """Same as ``.read``, but makes AsyncBidirectionalStream
        eligible to be used as AsyncIterator."""

        try:
            result = await self._read()
        except:
            await self._release()
            raise
        if result is None:
            raise StopAsyncIteration
        return result

    @doc_from(BaseBidirectionalStream._gen)
    async def gen(self) -> AsyncGenerator[ProtoModelResultTypeT]:
        async for chunk in self._gen():
            yield chunk

    @doc_from(BaseBidirectionalStream._done_writing)
    async def done_writing(self) -> None:
        await self._done_writing()

    def __aiter__(self) -> AsyncIterator[ProtoModelResultTypeT]:
        return self


class BidirectionalStreamMixin(
    Generic[
        ConfigTypeT,
        ProtoModelResultTypeT,
        RequestTypeT,
        ResponseTypeT,
        StubTypeT,
        InputTypeT
    ],
    BaseBidirectionalStream[
        ConfigTypeT,
        ProtoModelResultTypeT,
        RequestTypeT,
        ResponseTypeT,
        StubTypeT,
        InputTypeT
    ],
    Iterator[ProtoModelResultTypeT],
):
    __write = run_sync(BaseBidirectionalStream._write)
    __read = run_sync(BaseBidirectionalStream._read)
    __gen = run_sync_generator(BaseBidirectionalStream._gen)
    __done_writing = run_sync(BaseBidirectionalStream._done_writing)

    @doc_from(BaseBidirectionalStream._write)
    def write(self, input: InputTypeT) -> None:
        self.__write(input)

    @doc_from(BaseBidirectionalStream._read)
    def read(self) -> ProtoModelResultTypeT | None:
        return self.__read()

    def __next__(self) -> ProtoModelResultTypeT:
        """Same as ``.read``, but makes BidirectionalStream
        eligible to be used as Iterator."""

        result = self.__read()
        if result is None:
            raise StopIteration

        return result

    @doc_from(BaseBidirectionalStream._gen)
    def gen(self) -> Generator[ProtoModelResultTypeT]:
        yield from self.__gen()

    @doc_from(BaseBidirectionalStream._done_writing)
    def done_writing(self) -> None:
        self.__done_writing()

    def __iter__(self) -> Iterator[ProtoModelResultTypeT]:
        return self
