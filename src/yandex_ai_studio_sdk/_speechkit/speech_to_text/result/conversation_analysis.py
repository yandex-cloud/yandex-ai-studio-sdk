# pylint: disable=no-name-in-module,invalid-enum-extension,unused-argument
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import override
from yandex.cloud.ai.stt.v3.stt_pb2 import ConversationAnalysis as ProtoConversationAnalysis
from yandex_ai_studio_sdk._types.proto import ProtoMirrored, SDKType

from .descriptive_statistics import DescriptiveStatistics
from .utils import TimeSpan

ProtoInterruptsEvaluation = ProtoConversationAnalysis.InterruptsEvaluation


@dataclass(frozen=True)
class InterruptsEvaluation(ProtoMirrored[ProtoInterruptsEvaluation]):
    """Interrupt description"""

    #: Speaker tag.
    speaker_tag: str

    #: Number of interrupts made by the speaker.
    interrupts_count: int

    #: Total duration of all interrupts.
    interrupts_duration_ms: int

    #: Boundaries for every interrupt.
    interrupts: tuple[TimeSpan, ...]

    @override
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoInterruptsEvaluation, sdk: SDKType) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)
        kwargs['interrupts'] = tuple(
            TimeSpan(start_time_ms=i.start_time_ms, end_time_ms=i.end_time_ms)
            for i in proto.interrupts
        )
        return kwargs


@dataclass(frozen=True)
class ConversationAnalysis(ProtoMirrored[ProtoConversationAnalysis]):
    """Conversation statistics."""

    #: Audio segment boundaries
    timespan: TimeSpan

    #: Total simultaneous silence duration.
    total_simultaneous_silence_duration_ms: int

    #: Simultaneous silence ratio within audio segment.
    total_simultaneous_silence_ratio: float

    #: Descriptive statistics for simultaneous silence duration distribution.
    simultaneous_silence_duration_estimation: DescriptiveStatistics

    #: Total simultaneous speech duration.
    total_simultaneous_speech_duration_ms: int

    #: Simultaneous speech ratio within audio segment.
    total_simultaneous_speech_ratio: float

    #: Descriptive statistics for simultaneous speech duration distribution.
    simultaneous_speech_duration_estimation: DescriptiveStatistics

    #: Interrupts description for every speaker.
    speaker_interrupts: tuple[InterruptsEvaluation, ...]

    #: Total speech duration, including both simultaneous and separate speech.
    total_speech_duration_ms: int

    #: Total speech ratio within audio segment.
    total_speech_ratio: float

    @override
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoConversationAnalysis, sdk: SDKType) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)

        kwargs['timespan'] = TimeSpan(
            start_time_ms=proto.conversation_boundaries.start_time_ms,
            end_time_ms=proto.conversation_boundaries.end_time_ms
        )

        for field_name in (
            'simultaneous_speech_duration_estimation',
            'simultaneous_silence_duration_estimation',
        ):
            value = getattr(proto, field_name)
            new_value = DescriptiveStatistics._from_proto(proto=value, sdk=sdk)
            kwargs[field_name] = new_value

        kwargs['speaker_interrupts'] = tuple(
            InterruptsEvaluation._from_proto(proto=i, sdk=sdk)
            for i in proto.speaker_interrupts
        )

        return kwargs
