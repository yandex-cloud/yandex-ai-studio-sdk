# pylint: disable=no-name-in-module,invalid-enum-extension,unused-argument
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import overload

from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import Summarization
from yandex_ai_studio_sdk._models.completions.result import Usage
from yandex_ai_studio_sdk._speechkit.speech_to_text.config import SpeechToTextConfig
from yandex_ai_studio_sdk._types.proto import ProtoBasedWithCtx, SDKType
from yandex_ai_studio_sdk._types.request import RequestDetails


@dataclass(frozen=True)
class LLMPostProcessResult(ProtoBasedWithCtx[Summarization, RequestDetails[SpeechToTextConfig]], Sequence):
    """Result of the LLM postprocessing"""

    #: A set of statistics describing the number of content tokens used by the completion model.
    usage: Usage

    #: text results returned by model
    texts: tuple[str, ...]
    #: instructions given to model
    instructions: tuple[str, ...]

    @property
    def by_instructions(self) -> dict[str, str]:
        return dict(zip(self.instructions, self.texts))

    @classmethod
    @override
    def _from_proto(
        cls,
        *,
        proto: Summarization,
        sdk: SDKType,
        ctx: RequestDetails[SpeechToTextConfig]
    ) -> Self:
        instructions: tuple[str, ...]
        if config := ctx.model_config.llm_post_process:
            instructions = tuple(i.instruction for i in config.instructions)
        else:
            instructions = ('<sdk> somewhy instructions are missing',)

        return cls(
            texts=tuple(property.response for property in proto.results),
            instructions=instructions,
            usage=Usage(
                completion_tokens=proto.content_usage.completion_tokens,
                input_text_tokens=proto.content_usage.input_text_tokens,
                total_tokens=proto.content_usage.total_tokens,
            )
        )

    def __len__(self):
        return len(self.texts)

    @overload
    def __getitem__(self, index: int, /) -> str:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[str, ...]:
        pass

    def __getitem__(self, index, /):
        return self.texts[index]
