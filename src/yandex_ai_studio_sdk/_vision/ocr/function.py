from __future__ import annotations

from typing_extensions import override

from yandex_ai_studio_sdk._types.function import BaseModelFunction
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._utils.doc import doc_from

from .ocr import OCR, AsyncOCR, LanguageCodesInputType, OCRTypeT


class BaseOCRFunction(BaseModelFunction[OCRTypeT]):
    """OCR function for creating an OCR object which provides
    methods for invoking Yandex Vision OCR.
    """

    @override
    def __call__(
        self,
        *,
        language_codes: UndefinedOr[LanguageCodesInputType] | None = UNDEFINED,
        model: UndefinedOr[str] | None = UNDEFINED,
    ) -> OCRTypeT:
        """Creates an OCR object for working with Yandex Vision OCR API.

        Refer to `OCR documentation <https://aistudio.yandex.ru/docs/vision/concepts/ocr/>`_
        for more information.

        :param language_codes: List of languages to recognize text, in ISO 639-1 format
            (e.g. ``"ru"``, ``"en"``).
            See `supported languages <https://aistudio.yandex.ru/docs/vision/concepts/ocr/supported-languages.html>`_.
        :param model: Model to use for text recognition.
            General models: ``"page"`` (default), ``"page-column-sort"``, ``"handwritten"``,
            ``"table"``, ``"markdown"``, ``"math-markdown"``.
            Document template models: ``"passport"``, ``"driver-license-front"``,
            ``"driver-license-back"``, ``"vehicle-registration-front"``,
            ``"vehicle-registration-back"``, ``"license-plates"``.
            See `models <https://aistudio.yandex.ru/docs/vision/concepts/ocr/#models>`_ and
            `document recognition <https://aistudio.yandex.ru/docs/vision/concepts/ocr/template-recognition>`_.
        """
        ocr = self._model_type(sdk=self._sdk, uri='<vision-ocr>')
        return ocr.configure(
            language_codes=language_codes,
            model=model,
        )


@doc_from(BaseOCRFunction)
class OCRFunction(BaseOCRFunction[OCR]):
    _model_type = OCR


@doc_from(BaseOCRFunction)
class AsyncOCRFunction(BaseOCRFunction[AsyncOCR]):
    _model_type = AsyncOCR
