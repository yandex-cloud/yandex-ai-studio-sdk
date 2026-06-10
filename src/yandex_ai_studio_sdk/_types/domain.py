from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from get_annotations import get_annotations

from .function import BaseModelFunction

if TYPE_CHECKING:
    from yandex_ai_studio_sdk._client import AsyncCloudClient
    from yandex_ai_studio_sdk._sdk import BaseSDK


class BaseDomain:
    # TODO: add some repr, description and such
    def __init__(self, name: str, sdk: BaseSDK):
        self._name = name
        self._sdk = sdk

    @property
    def _client(self) -> AsyncCloudClient:
        return self._sdk._client

    @property
    def _folder_id(self) -> str:
        return self._sdk._folder_id


class DomainWithFunctions(BaseDomain):
    def __init__(self, name: str, sdk: BaseSDK):
        super().__init__(name=name, sdk=sdk)
        self._init_functions()

    def _get_members(self) -> Iterator[tuple[str, type[BaseModelFunction]]]:
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member_class in members.items():
            if issubclass(member_class, BaseModelFunction):
                yield (member_name, member_class)

    def _init_functions(self) -> None:
        for member_name, member_class in self._get_members():
            function = member_class(name=member_name, sdk=self._sdk, parent_resource=self)
            setattr(self, member_name, function)

    def __repr__(self) -> str:
        return '{}<{}>'.format(
            self.__class__.__name__,
            ', '.join((f"{k}: {v}") for k, v in self._get_members())
        )
