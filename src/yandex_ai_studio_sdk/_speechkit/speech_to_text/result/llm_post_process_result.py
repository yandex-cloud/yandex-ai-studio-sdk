# pylint: disable=no-name-in-module,invalid-enum-extension,unused-argument
from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import Summarization

from yandex_ai_studio_sdk._models.completions.result import Usage
from yandex_ai_studio_sdk._types.proto import ProtoBasedWithCtx, SDKType
from yandex_ai_studio_sdk._types.sequence import TupleSequence

from .context import RequestDetails


@dataclass(frozen=True)
class LLMPostProcessResult(TupleSequence[str], ProtoBasedWithCtx[Summarization, RequestDetails]):
    """Result of the LLM postprocessing"""

    #: A set of statistics describing the number of content tokens used by the completion model.
    usage: Usage

    #: text results returned by model
    texts: tuple[str, ...]
    #: instructions given to model
    instructions: tuple[str, ...] | None

    @override
    @property
    def _items(self) -> tuple[str, ...]:
        return self.texts

    @property
    def by_instructions(self) -> dict[str, str]:
        if not self.instructions:
            raise RuntimeError('by_instructions field is unavailable with deferred recognition')
        return dict(zip(self.instructions, self.texts))

    @classmethod
    @override
    def _from_proto(
        cls,
        *,
        proto: Summarization,
        sdk: SDKType,
        ctx: RequestDetails
    ) -> Self:
        instructions: tuple[str, ...] | None = None
        if ctx.model_config:
            if config := ctx.model_config.llm_post_process:
                instructions = tuple(i.instruction for i in config.instructions)

        return cls(
            texts=tuple(property.response for property in proto.results),
            instructions=instructions,
            usage=Usage(
                completion_tokens=proto.content_usage.completion_tokens,
                input_text_tokens=proto.content_usage.input_text_tokens,
                total_tokens=proto.content_usage.total_tokens,
            )
        )
