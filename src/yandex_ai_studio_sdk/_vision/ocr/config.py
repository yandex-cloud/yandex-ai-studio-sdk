from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import Self, override

from yandex_ai_studio_sdk._types.model_config import BaseModelConfig
from yandex_ai_studio_sdk._utils.coerce import coerce_tuple


@dataclass(frozen=True)
class OCRConfig(BaseModelConfig):
    """Object to hold OCR run configuration."""

    #: List of languages to recognize text, in ISO 639-1 format (e.g. ``"ru"``, ``"en"``).
    #: See `supported languages <https://aistudio.yandex.ru/docs/vision/concepts/ocr/supported-languages.html>`_.
    language_codes: tuple[str, ...] | None = None

    #: Model to use for text recognition.
    #:
    #: General recognition models:
    #:
    #: * ``"page"`` (default): Single-column text, any number of lines.
    #: * ``"page-column-sort"``: Multi-column text.
    #: * ``"handwritten"``: Combination of typed and handwritten text (Russian and English only).
    #: * ``"table"``: Tables (Russian and English only).
    #: * ``"markdown"``: Returns results in Markdown format.
    #: * ``"math-markdown"``: Math formulas; results include LaTeX-formatted expressions.
    #:
    #: Document template recognition models:
    #:
    #: * ``"passport"``: Main passport spread.
    #: * ``"driver-license-front"``: Driver's license, front side.
    #: * ``"driver-license-back"``: Driver's license, back side.
    #: * ``"vehicle-registration-front"``: Vehicle registration certificate, front side.
    #: * ``"vehicle-registration-back"``: Vehicle registration certificate, back side.
    #: * ``"license-plates"``: All license plates visible in the image.
    #:
    #: See `models <https://aistudio.yandex.ru/docs/vision/concepts/ocr/#models>`_ and
    #: `document recognition <https://aistudio.yandex.ru/docs/vision/concepts/ocr/template-recognition>`_
    #: for more details.
    model: str | None = None

    @override
    def _replace(self, **kwargs: Any) -> Self:
        if 'language_codes' in kwargs:
            language_codes = kwargs['language_codes']
            if language_codes is not None:
                kwargs['language_codes'] = coerce_tuple(language_codes, str)
        return super()._replace(**kwargs)
