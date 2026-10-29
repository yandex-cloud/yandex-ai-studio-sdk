from __future__ import annotations

from typing_extensions import override

from yandex_ai_studio_sdk._types.function import BaseModelFunction
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._types.string import SmartStringSequence
from yandex_ai_studio_sdk._utils.doc import doc_from

from .config import AVAILABLE_FORMATS, SmartFilterSequence
from .generative import AsyncGenerativeSearch, GenerativeSearch, GenerativeSearchTypeT


class BaseGenerativeSearchFunction(BaseModelFunction[GenerativeSearchTypeT]):
    """Generative search function for creating a search object which provides
    methods for invoking generative search.
    """

    @override
    def __call__(
        self,
        *,
        site: UndefinedOr[SmartStringSequence] = UNDEFINED,
        host: UndefinedOr[SmartStringSequence] = UNDEFINED,
        url: UndefinedOr[SmartStringSequence] = UNDEFINED,
        fix_misspell: UndefinedOr[bool] = UNDEFINED,
        enable_nrfm_docs: UndefinedOr[bool] = UNDEFINED,
        search_filters: UndefinedOr[SmartFilterSequence] = UNDEFINED
    ) -> GenerativeSearchTypeT:
        """
        Creates a generative search object which provides methods for invoking generative search.

        To learn more about parameters and their formats and possible values,
        refer to
        `generative search documentation <https://aistudio.yandex.ru/docs/search-api/concepts/generative-response#request>`_

        NB: All of the ``site``, ``host``, ``url`` parameters are mutually exclusive.

        :param site: parameter for limiting search to a specific site or list of sites.
        :param host: parameter for limiting search to a specific host or list of hosts.
        :param url: parameter for limiting search to a specific URL or list of URLs.
        :param fix_misspell: whether the backend should correct misspellings in queries.
        :param enable_nrfm_docs: whether the backend should include pages
            that cannot be reached directly from the specified sites, hosts, or URLs
            in the search results.
        :param search_filters: limits search results using additional filters.

            >>> date_filter = {'date': '<20250101'}
            >>> format_filter = {'format': 'doc'}
            >>> lang_filter = {'lang': 'ru'}
            >>> search = sdk.search_api.generative(search_filters=[date_filter, format_filter, lang_filter])

        """
        search_api = self._model_type(sdk=self._sdk, uri='<search_api>')

        return search_api.configure(
            site=site,
            host=host,
            url=url,
            fix_misspell=fix_misspell,
            enable_nrfm_docs=enable_nrfm_docs,
            search_filters=search_filters
        )

    @property
    def available_formats(self):
        return AVAILABLE_FORMATS


@doc_from(BaseGenerativeSearchFunction)
class GenerativeSearchFunction(BaseGenerativeSearchFunction[GenerativeSearch]):
    _model_type = GenerativeSearch


@doc_from(BaseGenerativeSearchFunction)
class AsyncGenerativeSearchFunction(BaseGenerativeSearchFunction[AsyncGenerativeSearch]):
    _model_type = AsyncGenerativeSearch
