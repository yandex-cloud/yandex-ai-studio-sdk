from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.stt.v3.stt_pb2 import StreamingResponse

from yandex_ai_studio_sdk._types.request import RequestDetails
from yandex_ai_studio_sdk._types.result import BaseProtoModelResult, SDKType

from .config import SpeechToTextConfig


@dataclass(frozen=True)
class SpeechToTextResult(BaseProtoModelResult[StreamingResponse, RequestDetails[SpeechToTextConfig]]):
    """A class representing result of speech recognition request.
    """

    _request_details: RequestDetails[SpeechToTextConfig] = field(repr=False)

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: StreamingResponse, sdk: SDKType, ctx: RequestDetails[SpeechToTextConfig]) -> Self:
        return cls(
            _request_details=ctx
        )

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        # pylint: disable-next=unused-argument
        sdk: SDKType,
        ctx: RequestDetails[SpeechToTextConfig]
    ) -> Self:
        print(proto)
        return cls(
            _request_details=ctx
        )
