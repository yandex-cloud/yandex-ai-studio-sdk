from __future__ import annotations

import datetime
import itertools
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from functools import cached_property
from types import MappingProxyType
from typing import ClassVar, Generic, Literal, TypeAlias, TypeVar, Union, overload

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.img_search_service_pb2 import ImageSearchResponse
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.search_service_pb2 import WebSearchResponse
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import GetRegionsTreeResponse

from yandex_ai_studio_sdk._types.model import BaseModel, ConfigTypeT
from yandex_ai_studio_sdk._types.proto import ProtoBased
from yandex_ai_studio_sdk._types.request import RequestDetails
from yandex_ai_studio_sdk._types.result import BaseProtoModelResult, ProtoMessageTypeT, SDKType
from yandex_ai_studio_sdk._types.sequence import TupleSequence
from yandex_ai_studio_sdk._types.xml import XMLBased

from .utils import get_subelement_text

XMLSearchProtoMessage: TypeAlias = Union[WebSearchResponse, ImageSearchResponse]
XMLSearchProtoMessageTypeT = TypeVar(
    'XMLSearchProtoMessageTypeT',
    bound=XMLSearchProtoMessage,
)


class SearchDocument:
    pass


@dataclass(frozen=True)
class XMLSearchDocument(SearchDocument, XMLBased):
    url: str | None
    domain: str | None
    modtime: datetime.datetime | None

    @staticmethod
    def _parse_modtime(data: ET.Element) -> datetime.datetime | None:
        if raw_modtime := get_subelement_text(data, 'modtime'):
            raw_modtime = raw_modtime.strip()
            try:
                return datetime.datetime.strptime(raw_modtime, '%Y%m%dT%H%M%S')
            except ValueError:
                pass

        return None


SearchDocumentTypeT = TypeVar('SearchDocumentTypeT', bound=SearchDocument)
XMLSearchDocumentTypeT = TypeVar('XMLSearchDocumentTypeT', bound=XMLSearchDocument)


@dataclass(frozen=True)
class SearchRequestDetails(RequestDetails[ConfigTypeT]):
    """:meta private:

    Object to incapsulate search settings into search result
    to make possible .next_page methods"""

    page: int
    query: str


@dataclass(frozen=True)
class SearchGroup(TupleSequence[XMLSearchDocumentTypeT], XMLBased, Generic[XMLSearchDocumentTypeT]):
    documents: tuple[XMLSearchDocumentTypeT, ...]

    @override
    @property
    def _items(self) -> tuple[XMLSearchDocumentTypeT, ...]:
        return self.documents

    @classmethod
    def _from_xml(
        cls,
        *,
        data: ET.Element,
        sdk: SDKType,
        document_type: type[XMLSearchDocumentTypeT] | None = None,
    ) -> SearchGroup[XMLSearchDocumentTypeT]:
        assert document_type
        return cls(
            documents=tuple(
                document_type._from_xml(data=el, sdk=sdk)
                for el in data.iter('doc')
            )
        )


@dataclass(frozen=True)
class BaseSearchResult(
    TupleSequence[SearchDocumentTypeT],
    Generic[ProtoMessageTypeT, SearchDocumentTypeT, ConfigTypeT],
    BaseProtoModelResult[ProtoMessageTypeT, SearchRequestDetails[ConfigTypeT]],
    ABC
):
    _sdk: SDKType = field(repr=False)
    _request_details: SearchRequestDetails[ConfigTypeT] = field(repr=False)

    #: Returned search page number.
    page: int

    @property
    @abstractmethod
    def docs(self) -> tuple[SearchDocumentTypeT, ...]:
        """Returns all documents within search response."""

    @override
    @property
    def _items(self) -> tuple[SearchDocumentTypeT, ...]:
        return self.docs

    @property
    @abstractmethod
    def _model(self) -> BaseModel:
        pass

    @abstractmethod
    async def _next_page(self, *, timeout: float | None = None) -> Self:
        pass


@dataclass(frozen=True)
class XMLBaseSearchResult(
    BaseSearchResult[XMLSearchProtoMessageTypeT, XMLSearchDocumentTypeT, ConfigTypeT]
):
    #: Non-parsed XML result of search request.
    xml: bytes = field(repr=False)
    #: Parsed values of <group> tags within the response.
    groups: tuple[SearchGroup[XMLSearchDocumentTypeT], ...]
    _document_type: ClassVar[type[XMLSearchDocumentTypeT]]

    @override
    @classmethod
    def _from_proto(
        cls,
        *,
        proto: XMLSearchProtoMessageTypeT,
        sdk: SDKType,
        ctx: SearchRequestDetails[ConfigTypeT],
    ) -> Self:
        decoded = proto.raw_data.decode('utf-8')
        tree_root = ET.fromstring(decoded)

        response_data = tree_root.find('response')
        if response_data is not None:
            groups = tuple(
                SearchGroup[XMLSearchDocumentTypeT]._from_xml(
                    data=el, sdk=sdk, document_type=cls._document_type,
                )
                for el in response_data.iter('group')
            )
        else:
            groups = ()

        return cls(
            _sdk=sdk,
            _request_details=ctx,
            groups=groups,
            page=ctx.page,
            xml=proto.raw_data
        )

    @cached_property
    def docs(self) -> tuple[XMLSearchDocumentTypeT, ...]:
        """Returns all documents within search response."""
        return tuple(itertools.chain.from_iterable(self.groups))


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

    @classmethod
    def _coerce_to_str(cls, value: Region | str) -> str:
        if isinstance(value, Region):
            return value.id
        return value


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
