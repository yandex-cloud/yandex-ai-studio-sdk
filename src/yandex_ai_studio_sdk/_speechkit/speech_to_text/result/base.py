from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from yandex_ai_studio_sdk._types.result import BaseResult, SDKType

from .conversation_analysis import ConversationAnalysis
from .llm_post_process_result import LLMPostProcessResult


@dataclass(frozen=True)
class BaseSpeechToTextResult(BaseResult):
    _sdk: SDKType = field(repr=False)

    #: Field role is required to be compatible with TextMessage Protocol, to
    #: other part of SDK could use this object an input.
    role: ClassVar[str] = 'user'

    #: Internal session identifier.
    uuid: str
    #: User session identifier.
    user_request_id: str
    #: Conversation statistics
    conversation_analysis: ConversationAnalysis | None
    #: Result of llm post_process, may be also known as `Summarization` at some old documentation.
    llm_post_process_result: LLMPostProcessResult | None
