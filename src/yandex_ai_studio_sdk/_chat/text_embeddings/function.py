from __future__ import annotations

from typing import cast

from yandex_ai_studio_sdk._chat.base_function import BaseChatFunction, ModelTypeT
from yandex_ai_studio_sdk._chat.utils import ModelFilter
from yandex_ai_studio_sdk._utils.sync import run_sync

from .model import AsyncChatEmbeddingsModel, ChatEmbeddingsModel


class BaseChatEmbeddings(BaseChatFunction[ModelTypeT]):
    """Access text embeddings models through the OpenAI-compatible API.

    See the `available models and URI formats
    <https://aistudio.yandex.ru/docs/ai-studio/concepts/embeddings#yandexgpt-embeddings>`__
    and the `embeddings search example
    <https://aistudio.yandex.ru/docs/ai-studio/concepts/embeddings#example>`__
    in the AI Studio documentation.
    """
    _prefix = 'emb'


class ChatEmbeddings(BaseChatEmbeddings[ChatEmbeddingsModel]):
    __doc__ = BaseChatEmbeddings.__doc__

    _model_type = ChatEmbeddingsModel

    __list = run_sync(BaseChatEmbeddings[ChatEmbeddingsModel]._list)

    def list(
        self,
        *,
        timeout: float = 60,
        filters: ModelFilter | None = None
    ) -> tuple[ChatEmbeddingsModel, ...]:
        return cast(
            tuple[ChatEmbeddingsModel, ...],
            self.__list(timeout=timeout, filters=filters)
        )


class AsyncChatEmbeddings(BaseChatEmbeddings[AsyncChatEmbeddingsModel]):
    __doc__ = BaseChatEmbeddings.__doc__

    _model_type = AsyncChatEmbeddingsModel

    async def list(
        self,
        *,
        timeout: float = 60,
        filters: ModelFilter | None = None
    ) -> tuple[AsyncChatEmbeddingsModel, ...]:
        return await self._list(timeout=timeout, filters=filters)
