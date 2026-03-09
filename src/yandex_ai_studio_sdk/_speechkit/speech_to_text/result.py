# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TypeVar

from google.protobuf.empty_pb2 import Empty
from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import DeleteRecognitionRequest, StreamingResponse
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import AsyncRecognizerStub
from yandex_ai_studio_sdk._types.request import RequestDetails
from yandex_ai_studio_sdk._types.result import BaseProtoModelResult, BaseProtoResult, SDKType
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import SpeechToTextConfig


@dataclass(frozen=True)
class SpeechToTextResult(BaseProtoResult[StreamingResponse]):
    """A class representing result of speech recognition request.
    """

    _sdk: SDKType = field(repr=False)

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    def _from_proto(cls, *, proto: StreamingResponse, sdk: SDKType) -> Self:
        print(proto)
        return cls(
            _sdk=sdk,
        )

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        sdk: SDKType,
    ) -> Self:
        print(proto)
        return cls(
            _sdk=sdk,
        )


@dataclass(frozen=True)
class DeferredSpeechToTextBaseResult(SpeechToTextResult):
    operation_id: str

    async def _delete(self, timeout: float = 60) -> None:
        """Deletes results of asynchronous recognition."""

        request = DeleteRecognitionRequest(operation_id=self.operation_id)
        async with self._sdk._client.get_service_stub(AsyncRecognizerStub, timeout=timeout) as stub:
            await self._sdk._client.call_service(
                stub.DeleteRecognition,
                request,
                timeout=timeout,
                expected_type=Empty
            )

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    def _from_proto(
        cls,
        *,
        proto: StreamingResponse,
        sdk: SDKType,
        operation_id: str | None = None
    ) -> Self:
        assert operation_id
        raw_result = SpeechToTextResult._from_proto(proto=proto, sdk=sdk)

        return cls(
            operation_id=operation_id,
            _sdk=raw_result._sdk,
        )

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        sdk: SDKType,
        operation_id: str | None = None
    ) -> Self:
        assert operation_id
        raw_result = SpeechToTextResult._from_proto_iterable(proto=proto, sdk=sdk)
        return cls(
            operation_id=operation_id,
            _sdk=raw_result._sdk,
        )


class AsyncDeferredSpeechToTextResult(DeferredSpeechToTextBaseResult):
    @doc_from(DeferredSpeechToTextBaseResult._delete)
    async def delete(self, timeout: float = 60) -> None:
        await self._delete(timeout=timeout)


class DeferredSpeechToTextResult(DeferredSpeechToTextBaseResult):
    __delete = run_sync(DeferredSpeechToTextBaseResult._delete)

    @doc_from(DeferredSpeechToTextBaseResult._delete)
    def delete(self, timeout: float = 60) -> None:
        self.__delete(timeout=timeout)


@dataclass(frozen=True)
class SpeechToTextStreamingEvent(BaseProtoModelResult[StreamingResponse, RequestDetails[SpeechToTextConfig]]):
    """A class representing streaming event of speech recognition request."""

    _sdk: SDKType = field(repr=False)

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    def _from_proto(cls, *, proto: StreamingResponse, sdk: SDKType, ctx: RequestDetails[SpeechToTextConfig]) -> Self:
        print(proto)
        return cls(
            _sdk=sdk,
        )


DeferredSpeechToTextResultTypeT = TypeVar(
    'DeferredSpeechToTextResultTypeT',
    bound=DeferredSpeechToTextBaseResult
)
