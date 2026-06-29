# pylint: disable=no-name-in-module,invalid-enum-extension
from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import CodeType as ProtoCodeType
from yandex.cloud.ai.stt.v3.stt_pb2 import StatusCode as ProtoStatusCode

from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, ProtoBasedEnum
from yandex_ai_studio_sdk._types.proto import ProtoBased, SDKType


class CodeType(ProtoBasedEnum):
    __proto_enum_type__ = ProtoCodeType
    __common_prefix__ = ''
    __unspecified_name__ = 'CODE_TYPE_UNSPECIFIED'

    #: All good.
    WORKING = ProtoCodeType.WORKING
    #: For example, if speech is sent not in real-time or context is unknown and we've made fallback.
    WARNING = ProtoCodeType.WARNING
    #: After session was closed.
    CLOSED = ProtoCodeType.CLOSED


@dataclass(frozen=True, repr=False)
class StatusCode(ProtoBased[ProtoStatusCode]):
    #: Human readable message
    message: str
    #: Code type
    code_type: EnumWithUnknownAlias[CodeType]

    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: ProtoStatusCode, sdk: SDKType) -> Self:
        return cls(
            message=proto.message,
            code_type=CodeType._coerce(proto.code_type)
        )

    def __repr__(self) -> str:
        parts = [self.code_type.name]

        if self.message:
            parts.append(self.message)

        return f'StatusCode<{", ".join(parts)}>'
