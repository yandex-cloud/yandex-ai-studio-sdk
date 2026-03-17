# pylint: disable=no-name-in-module,invalid-enum-extension,unused-argument
from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import PhraseHighlight as ProtoPhraseHighlight
from yandex.cloud.ai.stt.v3.stt_pb2 import RecognitionClassifierUpdate

from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, ProtoBasedEnum
from yandex_ai_studio_sdk._types.proto import ProtoBased, SDKType

from .utils import TimeSpan


@dataclass(frozen=True)
class PhraseHighlight(ProtoBased[ProtoPhraseHighlight]):
    #: Text transcription of the highlighted audio segment.
    text: str

    #: highlighted audio segment boundaries
    timespan: TimeSpan

    @classmethod
    @override
    def _from_proto(cls, *, proto: ProtoPhraseHighlight, sdk: SDKType) -> Self:
        return cls(
            text=proto.text,
            timespan=TimeSpan(start_time_ms=proto.start_time_ms, end_time_ms=proto.end_time_ms)
        )


@dataclass(frozen=True)
class ClassifierUpdate(ProtoBased[RecognitionClassifierUpdate]):
    """Result of the triggered classifier"""

    class WindowType(ProtoBasedEnum):
        __proto_enum_type__ = RecognitionClassifierUpdate.WindowType
        __common_prefix__ = ''
        __unspecified_name__ = 'WINDOW_TYPE_UNSPECIFIED'

        #: The result of applying the classifier to the last utterance response.
        LAST_UTTERANCE = RecognitionClassifierUpdate.WindowType.LAST_UTTERANCE
        #: The result of applying the classifier to the last final response.
        LAST_FINAL = RecognitionClassifierUpdate.WindowType.LAST_FINAL
        #: The result of applying the classifier to the last partial response.
        LAST_PARTIAL = RecognitionClassifierUpdate.WindowType.LAST_PARTIAL

    #: Response window type.
    window_type: EnumWithUnknownAlias[WindowType]

    #: Name of the triggered classifier.
    classifier: str

    #: List of highlights, i.e. parts of phrase that determine the result of the classification
    highlights: tuple[PhraseHighlight, ...]

    #: Classifier predictions
    labels: dict[str, float]

    #: Audio segment used for classification boundaries
    timespan: TimeSpan

    @property
    def confidence(self) -> float | None:
        """Synonym for easy access to 'confidence' label if it exists"""
        return self.labels.get('confidence')

    @classmethod
    @override
    def _from_proto(cls, *, proto: RecognitionClassifierUpdate, sdk: SDKType) -> Self:
        return cls(
            window_type=cls.WindowType._coerce(proto.window_type),
            classifier=proto.classifier_result.classifier,
            highlights=tuple(
                PhraseHighlight._from_proto(proto=highlight, sdk=sdk)
                for highlight in proto.classifier_result.highlights
            ),
            labels={
                label.label: label.confidence
                for label in proto.classifier_result.labels
            },
            timespan=TimeSpan(start_time_ms=proto.start_time_ms, end_time_ms=proto.end_time_ms)
        )
