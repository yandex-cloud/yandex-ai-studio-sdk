# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing import TypeVar

from typing_extensions import Self, override
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import GetRegionsTreeRequest, GetRegionsTreeResponse
from yandex.cloud.searchapi.v2.wordstat_service_pb2_grpc import WordstatServiceStub

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._types.model import BaseModel
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import WordstatConfig
from .result import BaseWordstatResult, RegionsTree

logger = get_logger(__name__)


class BaseWordstat(BaseModel[WordstatConfig, BaseWordstatResult]):
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


@doc_from(BaseWordstat)
class AsyncWordstat(BaseWordstat):
    @doc_from(BaseWordstat._get_regions_tree)
    async def get_regions_tree(self, timeout: float = 60) -> RegionsTree:
        return await self._get_regions_tree(timeout=timeout)


@doc_from(BaseWordstat)
class Wordstat(BaseWordstat):
    __get_regions_tree = run_sync(BaseWordstat._get_regions_tree)

    @doc_from(BaseWordstat._get_regions_tree)
    def get_regions_tree(self, timeout: float = 60) -> RegionsTree:
        return self.__get_regions_tree(timeout=timeout)


WordstatTypeT = TypeVar('WordstatTypeT', bound=BaseWordstat)
