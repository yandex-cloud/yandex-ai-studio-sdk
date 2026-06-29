from __future__ import annotations

from typing_extensions import override

from yandex_ai_studio_sdk._types.function import BaseModelFunction
from yandex_ai_studio_sdk._utils.doc import doc_from

from .wordstat import AsyncWordstat, Wordstat, WordstatTypeT


class BaseWordstatFunction(BaseModelFunction[WordstatTypeT]):
    """Wordstat function for creating wordstat object which provides
    methods for invoking Wordstat service.
    """

    @override
    def __call__(self) -> WordstatTypeT:
        """
        Creates Wordstat object which provides methods for invoking
        `Wordstat service <https://aistudio.yandex.ru/docs/ru/search-api/concepts/wordstat.html>`_.

        """
        wordstat = self._model_type(sdk=self._sdk, uri='<wordstat>')

        return wordstat


@doc_from(BaseWordstatFunction)
class WordstatFunction(BaseWordstatFunction[Wordstat]):
    _model_type = Wordstat


@doc_from(BaseWordstatFunction)
class AsyncWordstatFunction(BaseWordstatFunction[AsyncWordstat]):
    _model_type = AsyncWordstat
