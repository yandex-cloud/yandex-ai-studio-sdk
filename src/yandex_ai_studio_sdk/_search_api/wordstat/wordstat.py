# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

import datetime
from typing import TypeVar, cast

from typing_extensions import Self, override
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import (
    GetDynamicsRequest, GetDynamicsResponse, GetRegionsDistributionRequest, GetRegionsDistributionResponse,
    GetRegionsTreeRequest, GetRegionsTreeResponse, GetTopRequest, GetTopResponse
)
from yandex.cloud.searchapi.v2.wordstat_service_pb2_grpc import WordstatServiceStub

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._search_api.types import Region
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput
from yandex_ai_studio_sdk._types.misc import UNDEFINED, SmartIterable, UndefinedOr, is_defined
from yandex_ai_studio_sdk._types.model import BaseModel
from yandex_ai_studio_sdk._utils.coerce import coerce_tuple
from yandex_ai_studio_sdk._utils.datetime import to_timestamp
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import DeviceType, PeriodType, RegionsDistributionType, WordstatConfig
from .result import BaseWordstatResult, Dynamics, RegionsDistribution, RegionsDistributionContext, RegionsTree, Top
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

    @staticmethod
    def _coerce_regions(regions: UndefinedOr[SmartIterable[str | Region]]) -> list[str]:
        if is_defined(regions):
            return [
                Region._coerce_to_str(cast(str | Region, region))
                for region in coerce_tuple(regions, (str, Region))
            ]
        return []

    @staticmethod
    def _coerce_devices(devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]]) -> list[int]:
        if is_defined(devices):
            return [
                int(DeviceType._coerce(cast(EnumWithUnknownAlias[DeviceType], device)))
                for device in coerce_tuple(devices, (str, int, DeviceType))
            ]
        return []

    async def _get_top(
        self,
        phrase: str,
        num_phrases: int,
        *,
        regions: UndefinedOr[SmartIterable[str | Region]],
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]],
        timeout: float,
    ) -> Top:
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


        request = GetTopRequest(
            phrase=phrase,
            num_phrases=num_phrases,
            devices=self._coerce_devices(devices),  # type: ignore[arg-type]
            regions=self._coerce_regions(regions),
            folder_id=self._sdk._folder_id
        )
        async with self._client.get_service_stub(WordstatServiceStub, timeout=timeout) as stub:
            response: GetTopResponse = await self._client.call_service(
                stub.GetTop,
                request,
                timeout=timeout,
                expected_type=GetTopResponse
            )

        return Top._from_proto(
            proto=response,
            sdk=self._sdk
        )

    async def _get_dynamics(
        self,
        phrase: str,
        period: EnumWithUnknownInput[PeriodType],
        from_date: datetime.date | int | float,
        to_date: datetime.date | int | float,
        *,
        regions: UndefinedOr[SmartIterable[str | Region]],
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]],
        timeout: float,
     ) -> Dynamics:
        """
        The method returns the last 30 days data about popular queries containing the
        specified keyword and queries that are similar to the specified one.

        :param phrase: Keyword.
            The maximum string length in characters is 400.
        :param period: The period of aggregation of the number of queries
        :param from_date: The start of the period data is requested for.
             :py:class:`datetime.date` and :py:class:`datetime.datetime` without
             timezone, will be converted to timestamp with UTC timezone.
        :param to_date: The end of the period data is requested for.
             :py:class:`datetime.date` and :py:class:`datetime.datetime` without
             timezone, will be converted to timestamp with UTC timezone.
        :param regions: A list of regions or IDs of the regions a query was made from.
            The maximum number of elements is 100.
        :param devices: A list of device types a query was made from.
        """
        request = GetDynamicsRequest(
            phrase=phrase,
            period=PeriodType._coerce(period),  # type: ignore[arg-type]
            from_date=to_timestamp(from_date),
            to_date=to_timestamp(to_date),
            devices=self._coerce_devices(devices),  # type: ignore[arg-type]
            regions=self._coerce_regions(regions),
            folder_id=self._sdk._folder_id,
        )
        async with self._client.get_service_stub(WordstatServiceStub, timeout=timeout) as stub:
            response: GetDynamicsResponse = await self._client.call_service(
                stub.GetDynamics,
                request,
                timeout=timeout,
                expected_type=GetDynamicsResponse
            )

        return Dynamics._from_proto(
            proto=response,
            sdk=self._sdk
        )

    async def _get_regions_distribution(
        self,
        phrase: str,
        *,
        distribution_type: UndefinedOr[EnumWithUnknownInput[RegionsDistributionType]],
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]],
        resolve_regions: bool,
        timeout: float,
     ) -> RegionsDistribution:
        """
        The method returns the distribution of the number of queries
        containing the given keyword globally by region for the last 30 days.

        :param phrase: Keyword.
            The maximum string length in characters is 400.
        :param distribution_type: Show query distribution only by city, only by region, or everywhere.
        :param devices: A list of device types a query was made from.
        :param resolve_region: Should return a result with region_ids resolved into
            :py:class:`~.Region` objects.
            NB: resolving region means additional call of :py:method:`~.get_regions_distribution`
            method.
        """
        distribution_type_: EnumWithUnknownAlias[RegionsDistributionType] | None = None
        if is_defined(distribution_type):
            distribution_type_ = RegionsDistributionType._coerce(
                cast(EnumWithUnknownInput[RegionsDistributionType], distribution_type)
            )

        request = GetRegionsDistributionRequest(
            phrase=phrase,
            region=distribution_type_,   # type: ignore[arg-type]
            devices=self._coerce_devices(devices),  # type: ignore[arg-type]
            folder_id=self._sdk._folder_id,
        )
        async with self._client.get_service_stub(WordstatServiceStub, timeout=timeout) as stub:
            response: GetRegionsDistributionResponse = await self._client.call_service(
                stub.GetRegionsDistribution,
                request,
                timeout=timeout,
                expected_type=GetRegionsDistributionResponse,
            )

        regions_tree = None
        if resolve_regions:
            regions_tree = await self._get_regions_tree(timeout=timeout)

        return RegionsDistribution._from_proto(
            proto=response,
            sdk=self._sdk,
            ctx=RegionsDistributionContext(
                resolve_regions=resolve_regions,
                regions_tree=regions_tree,
            )
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
        regions: UndefinedOr[SmartIterable[str | Region]] = UNDEFINED,
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]] = UNDEFINED,
        timeout: float = 60,
    ) -> Top:
        return await self._get_top(
            phrase=phrase,
            num_phrases=num_phrases,
            regions=regions,
            devices=devices,
            timeout=timeout,
        )

    @doc_from(BaseWordstat._get_dynamics)
    async def get_dynamics(
        self,
        phrase: str,
        period: EnumWithUnknownInput[PeriodType],
        from_date: datetime.date | int | float,
        to_date: datetime.date | int | float,
        *,
        regions: UndefinedOr[SmartIterable[str | Region]] = UNDEFINED,
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]] = UNDEFINED,
        timeout: float = 60,
     ) -> Dynamics:
        return await self._get_dynamics(
            phrase=phrase,
            period=period,
            from_date=from_date,
            to_date=to_date,
            regions=regions,
            devices=devices,
            timeout=timeout
        )

    async def get_regions_distribution(
        self,
        phrase: str,
        *,
        distribution_type: UndefinedOr[EnumWithUnknownInput[RegionsDistributionType]] = UNDEFINED,
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]] = UNDEFINED,
        resolve_regions = False,
        timeout: float = 60,
     ) -> RegionsDistribution:
        return await self._get_regions_distribution(
            phrase=phrase,
            distribution_type=distribution_type,
            devices=devices,
            resolve_regions=resolve_regions,
            timeout=timeout,
        )



@doc_from(BaseWordstat)
class Wordstat(BaseWordstat):
    __get_regions_tree = run_sync(BaseWordstat._get_regions_tree)
    __get_top = run_sync(BaseWordstat._get_top)
    __get_dynamics = run_sync(BaseWordstat._get_dynamics)
    __get_regions_distribution = run_sync(BaseWordstat._get_regions_distribution)

    @doc_from(BaseWordstat._get_regions_tree)
    def get_regions_tree(self, timeout: float = 60) -> RegionsTree:
        return self.__get_regions_tree(timeout=timeout)

    @doc_from(BaseWordstat._get_top)
    def get_top(
        self,
        phrase: str,
        num_phrases: int,
        *,
        regions: UndefinedOr[SmartIterable[str | Region]] = UNDEFINED,
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]] = UNDEFINED,
        timeout: float = 60,
    ) -> Top:
        return self.__get_top(
            phrase=phrase,
            num_phrases=num_phrases,
            regions=regions,
            devices=devices,
            timeout=timeout,
        )

    @doc_from(BaseWordstat._get_dynamics)
    def get_dynamics(
        self,
        phrase: str,
        period: EnumWithUnknownInput[PeriodType],
        from_date: datetime.date | int | float,
        to_date: datetime.date | int | float,
        *,
        regions: UndefinedOr[SmartIterable[str | Region]] = UNDEFINED,
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]] = UNDEFINED,
        timeout: float = 60,
     ) -> Dynamics:
        return self.__get_dynamics(
            phrase=phrase,
            period=period,
            from_date=from_date,
            to_date=to_date,
            regions=regions,
            devices=devices,
            timeout=timeout
        )

    def get_regions_distribution(
        self,
        phrase: str,
        *,
        distribution_type: UndefinedOr[EnumWithUnknownInput[RegionsDistributionType]] = UNDEFINED,
        devices: UndefinedOr[SmartIterable[EnumWithUnknownInput[DeviceType]]] = UNDEFINED,
        resolve_regions = False,
        timeout: float = 60,
     ) -> RegionsDistribution:
        return self.__get_regions_distribution(
            phrase=phrase,
            distribution_type=distribution_type,
            devices=devices,
            resolve_regions=resolve_regions,
            timeout=timeout,
        )


WordstatTypeT = TypeVar('WordstatTypeT', bound=BaseWordstat)
