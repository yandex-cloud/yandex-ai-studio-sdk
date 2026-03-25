from __future__ import annotations

from yandex_ai_studio_sdk._types.domain import DomainWithFunctions
from yandex_ai_studio_sdk._utils.doc import doc_from

from .by_image.function import AsyncByImageSearchFunction, BaseByImageSearchFunction, ByImageSearchFunction
from .generative.function import AsyncGenerativeSearchFunction, BaseGenerativeSearchFunction, GenerativeSearchFunction
from .image.function import AsyncImageSearchFunction, BaseImageSearchFunction, ImageSearchFunction
from .web.function import AsyncWebSearchFunction, BaseWebSearchFunction, WebSearchFunction


class BaseSearchAPIDomain(DomainWithFunctions):
    """
    Domain for working with `Yandex Search API service <https://aistudio.yandex.ru/docs/search-api/concepts/index>`_.
    """

    #: API for `generative response <https://aistudio.yandex.ru/docs/search-api/concepts/generative-response>`_ service
    generative: BaseGenerativeSearchFunction
    #: API for `web search <https://aistudio.yandex.ru/docs/search-api/concepts/web-search>`_ service
    web: BaseWebSearchFunction
    #: API for `text image search <https://aistudio.yandex.ru/docs/search-api/concepts/image-search#search-by-text-query>`_ service
    image: BaseImageSearchFunction
    #: API for `search by image <https://aistudio.yandex.ru/docs/search-api/concepts/image-search#search-by-image>`_ service
    by_image: BaseByImageSearchFunction


@doc_from(BaseSearchAPIDomain)
class AsyncSearchAPIDomain(BaseSearchAPIDomain):
    generative: AsyncGenerativeSearchFunction
    web: AsyncWebSearchFunction
    image: AsyncImageSearchFunction
    by_image: AsyncByImageSearchFunction


@doc_from(BaseSearchAPIDomain)
class SearchAPIDomain(BaseSearchAPIDomain):
    generative: GenerativeSearchFunction
    web: WebSearchFunction
    image: ImageSearchFunction
    by_image: ByImageSearchFunction
