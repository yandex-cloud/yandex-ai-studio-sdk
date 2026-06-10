from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, overload

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import GetRegionsTreeResponse, GetTopResponse

from yandex_ai_studio_sdk._types.proto import ProtoBased, ProtoMessageTypeT
from yandex_ai_studio_sdk._types.result import BaseProtoResult, SDKType


@dataclass(frozen=True)
class BaseWordstatResult(BaseProtoResult[ProtoMessageTypeT]):
    """A class representing the result of a generative search request."""



@dataclass(frozen=True)
class GetTopResult(BaseWordstatResult[GetTopResponse]):
    @override
    @classmethod
    def _from_proto(cls, *, proto: GetTopResponse, sdk: SDKType) -> Self:
        return cls(
        )



@dataclass(frozen=True)
class Region(ProtoBased[GetRegionsTreeResponse.RegionInfo]):
    id: str
    label: str
    children: RegionsMapping | None

    @override
    @classmethod
    def _from_proto(cls, *, proto: GetRegionsTreeResponse.RegionInfo, sdk: SDKType) -> Self:
        children: RegionsMapping | None = None
        if proto.children:
            children = RegionsMapping._from_proto_iterable(proto=proto.children, sdk=sdk)

        return cls(
            id=proto.id,
            label=proto.label,
            children=children,
        )


@dataclass(frozen=True)
class RegionsMapping(Mapping[str, Region]):
    _regions: MappingProxyType[str, Region]

    @overload
    def __getitem__(self, key: str) -> Region:
        pass

    @overload
    def __getitem__(self, key: int) -> Region:
        pass

    def __getitem__(self, key: str | int) -> Region:
        return self._regions[str(key)]

    def __len__(self) -> int:
        return len(self._regions)

    def __iter__(self) -> Iterator[str]:
        return iter(self._regions)

    @classmethod
    def _from_proto_iterable(
        cls, *, proto: Iterable[GetRegionsTreeResponse.RegionInfo], sdk: SDKType
    ) -> Self:
        return cls(
            _regions=MappingProxyType({
                region.id: Region._from_proto(proto=region, sdk=sdk) for region in proto
                if region
            })
        )

    def dfs(self) -> Iterator[Region]:
        for region in self.values():
            yield region
            if region.children:
                yield from region.children.dfs()

    @overload
    def search_by_label(
        self,
        label: str,
        *,
        first: Literal[False] = False,
    ) -> tuple[Region]:
        pass

    @overload
    def search_by_label(
        self,
        label: str,
        *,
        first: Literal[True],
    ) -> Region | None:
        pass

    def search_by_label(
        self,
        label: str,
        *,
        first: bool = False
    ):
        result = []
        for region in self.dfs():
            if region.label == label:
                if first:
                    return region
                result.append(region)

        if first:
            return None
        return tuple(result)


@dataclass(frozen=True)
class RegionsTree(BaseProtoResult[GetRegionsTreeResponse], RegionsMapping):
    @override
    @classmethod
    def _from_proto(cls, *, proto: GetRegionsTreeResponse, sdk: SDKType) -> Self:
        return cls._from_proto_iterable(proto=proto.regions, sdk=sdk)
