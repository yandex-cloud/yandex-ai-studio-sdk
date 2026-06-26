from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.embedding.embedding_service_pb2 import TextEmbeddingResponse

from yandex_ai_studio_sdk._types.result import BaseProtoResult
from yandex_ai_studio_sdk._types.sequence import TupleSequence

if TYPE_CHECKING:
    from yandex_ai_studio_sdk._sdk import BaseSDK


@dataclass(frozen=True)
class TextEmbeddingsModelResult(TupleSequence[float], BaseProtoResult):
    """
    Represents the result of a text embeddings model.

    It holds the embedding vector, the number of tokens, and the
    version of the model that is used to generate embeggings.
    """
    #: the embedding vector as a tuple of floats
    embedding: tuple[float, ...]
    #: the number of tokens processed by the model
    num_tokens: int
    #: the version of the model used for generating embeddings
    model_version: str

    @override
    @property
    def _items(self) -> tuple[float, ...]:
        return self.embedding

    @classmethod
    def _from_proto(cls, *, proto: TextEmbeddingResponse, sdk: BaseSDK) -> Self:  # pylint: disable=unused-argument
        return cls(
            embedding=tuple(proto.embedding),
            num_tokens=proto.num_tokens,
            model_version=proto.model_version,
        )

    def __array__(self, dtype=None, copy=None):
        import numpy  # pylint: disable=import-outside-toplevel

        if copy is False:
            raise ValueError(
                "`copy=False` isn't supported. A copy is always created."
            )

        return numpy.array(self.embedding, dtype=dtype)
