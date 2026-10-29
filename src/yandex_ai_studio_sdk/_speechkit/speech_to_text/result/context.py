from __future__ import annotations

from dataclasses import dataclass

from yandex_ai_studio_sdk._speechkit.speech_to_text.config import SpeechToTextConfig
from yandex_ai_studio_sdk._types.proto import Context


@dataclass(frozen=True)
class RequestDetails(Context):
    """:meta private:

    Object that encapsulates a model request in a result
    to enable result methods which require context"""

    model_config: SpeechToTextConfig | None
