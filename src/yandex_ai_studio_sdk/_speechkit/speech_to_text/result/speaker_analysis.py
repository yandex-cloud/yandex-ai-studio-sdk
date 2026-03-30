# pylint: disable=no-name-in-module,invalid-enum-extension,unused-argument
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import override
from yandex.cloud.ai.stt.v3.stt_pb2 import SpeakerAnalysis as ProtoSpeakerAnalysis
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, ProtoBasedEnum
from yandex_ai_studio_sdk._types.proto import ProtoMirrored, SDKType

from .descriptive_statistics import DescriptiveStatistics
from .utils import TimeSpan


@dataclass(frozen=True)
class SpeakerAnalysis(ProtoMirrored[ProtoSpeakerAnalysis]):
    """Speech statistics for every speaker."""

    class WindowType(ProtoBasedEnum):
        __proto_enum_type__ = ProtoSpeakerAnalysis.WindowType
        __common_prefix__ = ''
        __unspecified_name__ = 'WINDOW_TYPE_UNSPECIFIED'

        #: Stats for last utterance
        LAST_UTTERANCE = ProtoSpeakerAnalysis.WindowType.LAST_UTTERANCE
        #: Stats for all received audio
        TOTAL = ProtoSpeakerAnalysis.WindowType.TOTAL

    #: Audio segment boundaries
    timespan: TimeSpan

    #:  Speaker tag.
    speaker_tag: str

    #:  Response window type.
    window_type: EnumWithUnknownAlias[WindowType]

    #:  Total speech duration.
    total_speech_ms: int

    #:  Speech ratio within audio segment.
    speech_ratio: float

    #:  Total duration of silence.
    total_silence_ms: int

    #:  Silence ratio within audio segment.
    silence_ratio: float

    #:  Number of words in recognized speech.
    words_count: int

    #:  Number of letters in recognized speech.
    letters_count: int

    #:  Descriptive statistics for words per second distribution.
    words_per_second: DescriptiveStatistics

    #:  Descriptive statistics for letters per second distribution.
    letters_per_second: DescriptiveStatistics

    #:  Descriptive statistics for words per utterance distribution.
    words_per_utterance: DescriptiveStatistics

    #:  Descriptive statistics for letters per utterance distribution.
    letters_per_utterance: DescriptiveStatistics

    #:  Number of utterances
    utterance_count: int

    #:  Descriptive statistics for utterance duration distribution
    utterance_duration_estimation: DescriptiveStatistics

    @override
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoSpeakerAnalysis, sdk: SDKType) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)

        kwargs['window_type'] = cls.WindowType._coerce(proto.window_type)
        kwargs['timespan'] = TimeSpan(
            start_time_ms=proto.speech_boundaries.start_time_ms,
            end_time_ms=proto.speech_boundaries.end_time_ms
        )

        for field_name in (
            'words_per_second',
            'letters_per_second',
            'words_per_utterance',
            'letters_per_utterance',
            'utterance_duration_estimation',
        ):
            value = getattr(proto, field_name)
            new_value = DescriptiveStatistics._from_proto(proto=value, sdk=sdk)
            kwargs[field_name] = new_value

        return kwargs
