from __future__ import annotations

import datetime
from dataclasses import dataclass
from types import MappingProxyType

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import (
    GetDynamicsResponse, GetRegionsDistributionResponse, GetRegionsTreeResponse, GetTopResponse
)

from yandex_ai_studio_sdk._search_api.types import Region, RegionsMapping
from yandex_ai_studio_sdk._types.proto import Context, ProtoMessageTypeT
from yandex_ai_studio_sdk._types.result import BaseProtoModelResult, BaseProtoResult, SDKType
from yandex_ai_studio_sdk._types.sequence import TupleSequence


@dataclass(frozen=True)
class BaseWordstatResult(BaseProtoResult[ProtoMessageTypeT]):
    """A class representing the result of a generative search request."""



@dataclass(frozen=True)
class Top(BaseWordstatResult[GetTopResponse]):
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
class DynamicsItem:
    date: datetime.date
    share: float
    count: int


@dataclass(frozen=True)
class Dynamics(TupleSequence[DynamicsItem], BaseWordstatResult[GetDynamicsResponse]):
    dynamics: tuple[DynamicsItem, ...]

    @override
    @property
    def _items(self) -> tuple[DynamicsItem, ...]:
        return self.dynamics

    @override
    @classmethod
    def _from_proto(cls, *, proto: GetDynamicsResponse, sdk: SDKType) -> Self:
        return cls(
            dynamics=tuple(
                DynamicsItem(
                    date=result.date.ToDatetime(tzinfo=datetime.timezone.utc).date(),
                    share=result.share,
                    count=result.count
                ) for result in proto.results
            )
        )


@dataclass(frozen=True)
class RegionItem:
    region: Region | None
    region_id: str
    count: int
    share: float
    affinity_index: float


@dataclass(frozen=True)
class RegionsDistributionContext(Context):
    resolve_regions: bool
    regions_tree: RegionsTree | None


@dataclass(frozen=True)
class RegionsDistribution(
    TupleSequence[RegionItem],
    BaseProtoModelResult[GetRegionsDistributionResponse, RegionsDistributionContext],
):
    _distribution: tuple[RegionItem, ...]

    @override
    @property
    def _items(self) -> tuple[RegionItem, ...]:
        return self._distribution

    @override
    @classmethod
    def _from_proto(
        cls,
        *,
        proto: GetRegionsDistributionResponse,
        sdk: SDKType,
        ctx: RegionsDistributionContext,
    ) -> Self:
        distribution: tuple[RegionItem, ...]

        regions_map = {}
        if ctx.resolve_regions:
            assert ctx.regions_tree
            regions_map = {region.id: region for region in ctx.regions_tree.dfs()}

        distribution = tuple(
            RegionItem(
                region=regions_map.get(line.region),
                region_id=line.region,
                affinity_index=line.affinity_index,
                count=line.count,
                share=line.share,
            ) for line in proto.results
        )

        return cls(
            _distribution=distribution
        )


@dataclass(frozen=True)
class RegionsTree(BaseProtoResult[GetRegionsTreeResponse], RegionsMapping):
    @override
    @classmethod
    def _from_proto(cls, *, proto: GetRegionsTreeResponse, sdk: SDKType) -> Self:
        return cls._from_proto_iterable(proto=proto.regions, sdk=sdk)
