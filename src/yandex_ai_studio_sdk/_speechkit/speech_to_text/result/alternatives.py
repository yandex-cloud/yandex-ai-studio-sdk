# pylint: disable=no-name-in-module,invalid-enum-extension,unused-argument
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import Alternative as ProtoAlternative
from yandex.cloud.ai.stt.v3.stt_pb2 import AlternativeUpdate
from yandex.cloud.ai.stt.v3.stt_pb2 import FinalRefinement as ProtoFinalRefinement
from yandex.cloud.ai.stt.v3.stt_pb2 import Word as ProtoWord

from yandex_ai_studio_sdk._types.proto import ProtoBased, ProtoMirrored, SDKType
from yandex_ai_studio_sdk._types.sequence import TupleSequence

from .utils import TimeSpan


@dataclass(frozen=True)
class Word(ProtoBased[ProtoWord]):
    """Recognized word"""

    #: Word text.
    text: str

    #: Estimation of word boundaries
    timespan: TimeSpan

    @classmethod
    @override
    def _from_proto(cls, *, proto: ProtoWord, sdk: SDKType) -> Self:
        return cls(
            text=proto.text,
            timespan=TimeSpan(start_time_ms=proto.start_time_ms, end_time_ms=proto.end_time_ms)
        )


@dataclass(frozen=True)
class Alternative(ProtoMirrored[ProtoAlternative]):
    """Recognition of specific time frame."""

    #: Words in time frame.
    words: tuple[Word, ]

    #: Text in time frame.
    text: str

    #: The hypothesis confidence. Currently is not used.
    confidence: float

    #: Distribution over possible languages.
    languages: dict[str, float] | None

    #: alternative's time frame
    timespan: TimeSpan

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoAlternative, sdk: SDKType) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)
        kwargs['languages'] = {
            lang.language_code: lang.probability
            for lang in proto.languages
        } if proto.languages else None
        kwargs['words'] = tuple(
            Word._from_proto(proto=word, sdk=sdk)
            for word in proto.words
        )
        kwargs['timespan'] = TimeSpan(start_time_ms=proto.start_time_ms, end_time_ms=proto.end_time_ms)
        return kwargs


@dataclass(frozen=True)
class BaseAlternatives(TupleSequence[Alternative]):
    alternatives: tuple[Alternative, ...]

    @override
    @property
    def _items(self) -> tuple[Alternative, ...]:
        return self.alternatives

    @property
    def words(self) -> tuple[Word, ]:
        """Synonym for .words attribute of first alternative"""
        return self.alternatives[0].words

    @property
    def text(self) -> str:
        """Synonym for .text attribute of first alternative"""
        return self.alternatives[0].text

    @property
    def timespan(self) -> TimeSpan:
        """Synonym for .timespan attribute of first alternative"""
        return self.alternatives[0].timespan

    @property
    def confidence(self) -> float:
        """Synonym for .confidence attribute of first alternative"""
        return self.alternatives[0].confidence

    @property
    def languages(self) -> dict[str, float] | None:
        """Synonym for .languages attribute of first alternative"""
        return self.alternatives[0].languages


class Alternatives(BaseAlternatives, ProtoBased[AlternativeUpdate]):
    """Class-wrapper for :py:class:`Alternative` list,
    which is allows to use this object not only as list,
    but as first Alternative."""

    @classmethod
    @override
    def _from_proto(cls, *, proto: AlternativeUpdate, sdk: SDKType) -> Self:
        return cls(
            alternatives=tuple(
                Alternative._from_proto(proto=a, sdk=sdk)
                for a in proto.alternatives
            )
        )

    def __repr__(self) -> str:
        alternatives = ', '.join(str(a) for a in self.alternatives)
        return f'Alternatives(({alternatives},))'


@dataclass(frozen=True)
class FinalRefinement(BaseAlternatives, ProtoBased[ProtoFinalRefinement]):
    """Class-wrapper for :py:class:`Alternative` list,
    which is allows to use this object not only as list,
    but as first Alternative."""

    final_index: int

    @classmethod
    @override
    def _from_proto(cls, *, proto: ProtoFinalRefinement, sdk: SDKType) -> Self:
        alternatives = Alternatives._from_proto(proto=proto.normalized_text, sdk=sdk).alternatives
        return cls(
            alternatives=alternatives,
            final_index=proto.final_index,
        )

    def __repr__(self) -> str:
        alternatives = ', '.join(str(a) for a in self.alternatives)
        return f'FinalRefinement(({alternatives},), final_index={self.final_index!r})'
