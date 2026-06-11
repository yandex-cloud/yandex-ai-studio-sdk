# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing import TypeVar, cast

from typing_extensions import Self, override
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import (
    GetRegionsTreeRequest, GetRegionsTreeResponse, GetTopRequest, GetTopResponse
)
from yandex.cloud.searchapi.v2.wordstat_service_pb2_grpc import WordstatServiceStub

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._search_api.types import Region
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput
from yandex_ai_studio_sdk._types.misc import (
    UNDEFINED, SmartSequence, UndefinedOr, coerce_sequence, get_defined_value, is_defined
)
from yandex_ai_studio_sdk._types.model import BaseModel
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import Device, WordstatConfig
from .result import BaseWordstatResult, GetTopResult, RegionsTree
from .synonyms import SynonymsMixin

logger = get_logger(__name__)


class BaseWordstat(BaseModel[WordstatConfig, BaseWordstatResult], SynonymsMixin):
    """Wordstat class which provides concrete methods for working with
    Wordstat service.
    """

    _config_type = WordstatConfig
    _result_type = BaseWordstatResult

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(self) -> Self:  # type: ignore[override]
        """
        Returns the new object, but actually do nothing.
        """

        return super().configure()

    @override
    def __repr__(self) -> str:
        # WordStat doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'

    async def _get_regions_tree(self, timeout: float) -> RegionsTree:
        """Return a tree of Wordstat-supported regions."""

        async with self._client.get_service_stub(WordstatServiceStub, timeout=timeout) as stub:
            response: GetRegionsTreeResponse = await self._client.call_service(
                stub.GetRegionsTree,
                GetRegionsTreeRequest(folder_id=self._sdk._folder_id),
                timeout=timeout,
                expected_type=GetRegionsTreeResponse
            )

        return RegionsTree._from_proto(
            proto=response,
            sdk=self._sdk
        )

    async def _get_top(
        self,
        phrase: str,
        num_phrases: int,
        *,
        regions: UndefinedOr[SmartSequence[str | Region]],
        devices: UndefinedOr[SmartSequence[EnumWithUnknownInput[Device]]],
        timeout: float,
    ) -> GetTopResult:
        """
        The method returns the last 30 days data about popular queries containing the
        specified keyword and queries that are similar to the specified one.

        :param phrase: Keyword.
            The maximum string length in characters is 400.
        :param num_phrases: Number of the phrases in the response.
            Acceptable values are 1 to 2000, inclusive.
        :param regions: A list of regions or IDs of the regions a query was made from.
            The maximum number of elements is 100.
        :param devices: A list of device types a query was made from.
        """

        regions_: list[str] | None = None
        if is_defined(regions):
            regions_ = [
                Region._coerce_to_str(cast(str | Region, region))
                for region in coerce_sequence(regions)
            ]

        devices_: list[EnumWithUnknownAlias[Device]] | None = None
        if is_defined(devices):
            devices_ = [
                Device._coerce(cast(EnumWithUnknownAlias[Device], device))
                for device in coerce_sequence(devices)
            ]

        request = GetTopRequest(
            phrase=phrase,
            num_phrases=num_phrases,
            devices=devices_,  # type: ignore[arg-type]
            regions=regions_,
            folder_id=self._sdk._folder_id
        )
        async with self._client.get_service_stub(WordstatServiceStub, timeout=timeout) as stub:
            response: GetTopResponse = await self._client.call_service(
                stub.GetTop,
                request,
                timeout=timeout,
                expected_type=GetTopResponse
            )

        return GetTopResult._from_proto(
            proto=response,
            sdk=self._sdk
        )


@doc_from(BaseWordstat)
class AsyncWordstat(BaseWordstat):
    @doc_from(BaseWordstat._get_regions_tree)
    async def get_regions_tree(self, timeout: float = 60) -> RegionsTree:
        return await self._get_regions_tree(timeout=timeout)

    @doc_from(BaseWordstat._get_top)
    async def get_top(
        self,
        phrase: str,
        num_phrases: int,
        *,
        regions: UndefinedOr[SmartSequence[str | Region]] = UNDEFINED,
        devices: UndefinedOr[SmartSequence[EnumWithUnknownInput[Device]]] = UNDEFINED,
        timeout: float = 60,
    ) -> GetTopResult:
        return await self._get_top(
            phrase=phrase,
            num_phrases=num_phrases,
            regions=regions,
            devices=devices,
            timeout=timeout,
        )


@doc_from(BaseWordstat)
class Wordstat(BaseWordstat):
    __get_regions_tree = run_sync(BaseWordstat._get_regions_tree)
    __get_top = run_sync(BaseWordstat._get_top)

    @doc_from(BaseWordstat._get_regions_tree)
    def get_regions_tree(self, timeout: float = 60) -> RegionsTree:
        return self.__get_regions_tree(timeout=timeout)

    @doc_from(BaseWordstat._get_top)
    def get_top(
        self,
        phrase: str,
        num_phrases: int,
        *,
        regions: UndefinedOr[SmartSequence[str | Region]] = UNDEFINED,
        devices: UndefinedOr[SmartSequence[EnumWithUnknownInput[Device]]] = UNDEFINED,
        timeout: float = 60,
    ) -> GetTopResult:
        return self.__get_top(
            phrase=phrase,
            num_phrases=num_phrases,
            regions=regions,
            devices=devices,
            timeout=timeout,
        )


WordstatTypeT = TypeVar('WordstatTypeT', bound=BaseWordstat)
