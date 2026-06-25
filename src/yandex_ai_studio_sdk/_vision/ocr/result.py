# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from typing_extensions import override
from yandex.cloud.ai.ocr.v1.ocr_service_pb2 import RecognizeTextResponse

from yandex_ai_studio_sdk._types.proto import SDKType
from yandex_ai_studio_sdk._types.result import BaseResult
from yandex_ai_studio_sdk._types.sequence import TupleSequence
from yandex_ai_studio_sdk._vision.ocr.text_annotation import PageContext, TextAnnotation


@dataclass(frozen=True, kw_only=True)
class OCRResult(TupleSequence[TextAnnotation], BaseResult):
    """Recognition result containing all recognized pages."""

    pages: tuple[TextAnnotation, ...]

    @property
    @override
    def _items(self) -> tuple[TextAnnotation, ...]:
        return self.pages

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[RecognizeTextResponse],
        sdk: SDKType,
    ) -> OCRResult:
        pages = tuple(
            TextAnnotation._from_proto(proto=p.text_annotation, sdk=sdk, ctx=PageContext(page=p.page))
            for p in proto
        )
        return cls(pages=pages)
