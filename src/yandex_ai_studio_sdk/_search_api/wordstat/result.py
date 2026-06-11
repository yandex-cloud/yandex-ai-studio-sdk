from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import GetRegionsTreeResponse, GetTopResponse

from yandex_ai_studio_sdk._search_api.types import RegionsMapping
from yandex_ai_studio_sdk._types.proto import ProtoMessageTypeT
from yandex_ai_studio_sdk._types.result import BaseProtoResult, SDKType


@dataclass(frozen=True)
class BaseWordstatResult(BaseProtoResult[ProtoMessageTypeT]):
    """A class representing the result of a generative search request."""



@dataclass(frozen=True)
class GetTopResult(BaseWordstatResult[GetTopResponse]):
    results: MappingProxyType[str, int]
    associations: MappingProxyType[str, int]

    @override
    @classmethod
    def _from_proto(cls, *, proto: GetTopResponse, sdk: SDKType) -> Self:
        return cls(
            results=MappingProxyType({result.phrase: result.count for result in proto.results}),
            associations=MappingProxyType({result.phrase: result.count for result in proto.associations}),
        )


@dataclass(frozen=True)
class RegionsTree(BaseProtoResult[GetRegionsTreeResponse], RegionsMapping):
    @override
    @classmethod
    def _from_proto(cls, *, proto: GetRegionsTreeResponse, sdk: SDKType) -> Self:
        return cls._from_proto_iterable(proto=proto.regions, sdk=sdk)
