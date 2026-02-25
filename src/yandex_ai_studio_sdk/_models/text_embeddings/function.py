from __future__ import annotations

from typing_extensions import override
from yandex_ai_studio_sdk._types.function import BaseModelFunction, ModelTypeT

from .model import AsyncTextEmbeddingsModel, TextEmbeddingsModel


class BaseTextEmbeddings(BaseModelFunction[ModelTypeT]):
    """
    A class for text embeddings models.

    It provides the functionality to call a text embeddings model
    either by a well-known name or a full URI.
    """
    _well_known_names = {
        'doc': 'text-search-doc',
        'query': 'text-search-query',
    }

    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ) -> ModelTypeT:
        """
        Call the specified model for text embeddings.
        It returns an instance of the specified type of the model.

        This method constructs the URI for the model based on the provided
        name and version. If the name contains ``://``, it is
        treated as a full URI. Otherwise, it looks up the model name in
        the well-known names dictionary. But after this, in any case,
        we construct a URI in the form ``emb://<folder_id>/<model>/<version>``.

        :param model_name: the name or URI of the model to call.
        :param model_version: the version of the model to use.
            Defaults to 'latest'.
        """

        return self._model_type(
            sdk=self._sdk,
            uri=self._sdk._get_model_uri('emb', model_name, model_version, self._well_known_names)
        )


class TextEmbeddings(BaseTextEmbeddings[TextEmbeddingsModel]):
    __doc__ = BaseTextEmbeddings.__doc__

    _model_type = TextEmbeddingsModel


class AsyncTextEmbeddings(BaseTextEmbeddings[AsyncTextEmbeddingsModel]):
    __doc__ = BaseTextEmbeddings.__doc__

    _model_type = AsyncTextEmbeddingsModel
