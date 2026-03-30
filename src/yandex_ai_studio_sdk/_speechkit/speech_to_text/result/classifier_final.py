from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self

from .classifier import ClassifierBase, ClassifierUpdate
from .event import SpeechToTextStreamingEvent


@dataclass(frozen=True)
class FinalClassifierResult(ClassifierBase):
    """Result of a classifier, tied to SpeechToTextResult object hierarchy and to specific final"""
    #: corresponding final event to on_final classifier result
    final: SpeechToTextStreamingEvent

    @classmethod
    def _from_classifier_update(cls, update: ClassifierUpdate, final: SpeechToTextStreamingEvent) -> Self:
        return cls(
            name=update.name,
            highlights=update.highlights,
            labels=update.labels,
            timespan=update.timespan,
            final=final,
        )
