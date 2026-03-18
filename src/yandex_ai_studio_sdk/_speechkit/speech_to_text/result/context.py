from __future__ import annotations

from dataclasses import dataclass

from yandex_ai_studio_sdk._speechkit.speech_to_text.config import SpeechToTextConfig
from yandex_ai_studio_sdk._types.proto import Context


@dataclass(frozen=True)
class RequestDetails(Context):
    """:meta private:

    Object to incapsulate model request into result
    to make possible result methods which requires a context"""

    model_config: SpeechToTextConfig | None
