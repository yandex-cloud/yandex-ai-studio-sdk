from __future__ import annotations

from yandex_ai_studio_sdk._types.domain import DomainWithFunctions
from yandex_ai_studio_sdk._utils.doc import doc_from

from .ocr.function import AsyncOCRFunction, BaseOCRFunction, OCRFunction


class BaseVisionDomain(DomainWithFunctions):
    """
    Domain for working with `Yandex Vision <https://aistudio.yandex.ru/docs/vision/concepts/ocr/>`_ services.
    """

    #: API for `OCR <https://aistudio.yandex.ru/docs/vision/concepts/ocr/>`_ service
    ocr: BaseOCRFunction


@doc_from(BaseVisionDomain)
class AsyncVisionDomain(BaseVisionDomain):
    ocr: AsyncOCRFunction


@doc_from(BaseVisionDomain)
class VisionDomain(BaseVisionDomain):
    ocr: OCRFunction
