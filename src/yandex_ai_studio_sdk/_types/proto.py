from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

from google.protobuf.message import Message as ProtoMessage
from typing_extensions import Self

from yandex_ai_studio_sdk._utils.proto import proto_to_dict

if TYPE_CHECKING:
    from yandex_ai_studio_sdk._sdk import BaseSDK

    SDKType: TypeAlias = BaseSDK
else:
    SDKType: TypeAlias = Any


class Context:
    pass


ProtoMessageTypeT = TypeVar('ProtoMessageTypeT', bound=ProtoMessage)
ContextTypeT = TypeVar('ContextTypeT', bound=Context)


class ProtoBased(abc.ABC, Generic[ProtoMessageTypeT]):
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT, sdk: BaseSDK) -> Self:
        raise NotImplementedError()


class ProtoBasedWithCtx(abc.ABC, Generic[ProtoMessageTypeT, ContextTypeT]):
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT, sdk: BaseSDK, ctx: ContextTypeT) -> Self:
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class ProtoMirrored(ProtoBased[ProtoMessageTypeT]):
    # pylint: disable=unused-argument
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoMessageTypeT, sdk: BaseSDK) -> dict[str, Any]:
        fields = dataclasses.fields(cls)
        data = proto_to_dict(proto)
        kwargs = {}
        for field in fields:
            name = field.name

            if name.startswith('_'):
                continue

            value = data.get(name)

            kwargs[name] = value

        return kwargs

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT, sdk: BaseSDK) -> Self:
        return cls(
            **cls._kwargs_from_message(proto, sdk=sdk),
        )
