# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Generic, TypeVar, Union

from google.protobuf.empty_pb2 import Empty
from typing_extensions import Self, override
from yandex.cloud.ai.ocr.v1.ocr_service_pb2 import GetRecognitionRequest, RecognizeTextRequest, RecognizeTextResponse
from yandex.cloud.ai.ocr.v1.ocr_service_pb2_grpc import TextRecognitionAsyncServiceStub, TextRecognitionServiceStub

from yandex_ai_studio_sdk._exceptions import AIStudioConfigurationError
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr, is_defined
from yandex_ai_studio_sdk._types.model import (
    ModelAsyncAttachMixin, ModelAsyncMixin, ModelSyncAttachMixin, ModelSyncMixin, OperationTypeT
)
from yandex_ai_studio_sdk._types.operation import AsyncOperation, Operation, OperationContext, ProtoOperation
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.mime import DetectMimeError
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import OCRConfig
from .result import OCRResult
from .utils import detect_mime_type

LanguageCodesInputType = Union[str, Sequence[str]]


class BaseOCR(
    Generic[OperationTypeT],
    ModelSyncMixin[OCRConfig, OCRResult],
    ModelAsyncMixin[OCRConfig, OCRResult, OperationTypeT],
):
    """OCR class which provides methods for working with Yandex Vision OCR API."""

    _config_type = OCRConfig
    _result_type = OCRResult
    _proto_result_type = Empty

    @override
    def configure(  # type: ignore[override]
        self,
        *,
        language_codes: UndefinedOr[LanguageCodesInputType] | None = UNDEFINED,
        model: UndefinedOr[str] | None = UNDEFINED,
    ) -> Self:
        """Returns the new object with config fields overridden by passed values.

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
        return super().configure(
            language_codes=language_codes,
            model=model,
        )

    def _make_request(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
    ) -> RecognizeTextRequest:
        c = self._config
        if is_defined(mime_type):
            resolved_mime_type = mime_type
        else:
            try:
                resolved_mime_type = detect_mime_type(content)
            except DetectMimeError as e:
                raise AIStudioConfigurationError(
                    f'{e} Please pass mime_type explicitly.'
                ) from e
        return RecognizeTextRequest(
            content=content,
            mime_type=resolved_mime_type,
            language_codes=list(c.language_codes) if c.language_codes else [],
            model=c.model or '',
        )

    async def _run_request(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
        timeout: float,
    ) -> AsyncIterator[RecognizeTextResponse]:
        request = self._make_request(content, mime_type=mime_type)

        async with self._client.get_service_stub(TextRecognitionServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.Recognize,
                request,
                timeout=timeout,
                expected_type=RecognizeTextResponse,
            ):
                yield response

    async def _operation_transformer(
        self,
        proto_result: Empty,  # pylint: disable=unused-argument
        timeout: float,
        ctx: OperationContext,
    ) -> OCRResult:
        protos = []
        async with self._client.get_service_stub(TextRecognitionAsyncServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.GetRecognition,
                GetRecognitionRequest(operation_id=ctx.id),
                timeout=timeout,
                expected_type=RecognizeTextResponse,
            ):
                protos.append(response)
        return OCRResult._from_proto_iterable(proto=protos, sdk=self._sdk)

    @override
    async def _run(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60,
    ) -> OCRResult:
        """Recognize text in the given image or PDF.

        Supported formats: JPEG, PNG, PDF.

        :param content: Raw bytes of the image or PDF file.
        :param mime_type: MIME type of the content (e.g. ``"image/jpeg"``, ``"image/png"``,
            ``"application/pdf"``). If not provided, will be detected automatically
            from the content magic bytes.
        :param timeout: Timeout in seconds.
        :returns: OCR result containing all recognized pages.
        """
        protos = [
            proto
            async for proto in self._run_request(content, mime_type=mime_type, timeout=timeout)
        ]
        return OCRResult._from_proto_iterable(proto=protos, sdk=self._sdk)

    @override
    async def _run_deferred(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60,
    ) -> OperationTypeT:
        """Recognize text in the given image or PDF asynchronously, returning an operation.

        Supported formats: JPEG, PNG, PDF.

        :param content: Raw bytes of the image or PDF file.
        :param mime_type: MIME type of the content (e.g. ``"image/jpeg"``, ``"image/png"``,
            ``"application/pdf"``). If not provided, will be detected automatically
            from the content magic bytes.
        :param timeout: Timeout in seconds.
        :returns: Operation that resolves to OCR result.
        """
        request = self._make_request(content, mime_type=mime_type)

        async with self._client.get_service_stub(TextRecognitionAsyncServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Recognize,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )

        return self._operation_type(
            sdk=self._sdk,
            id=response.id,
            proto_result_type=self._proto_result_type,
            result_type=self._result_type,
            transformer=self._operation_transformer,
        )


@doc_from(BaseOCR)
class AsyncOCR(BaseOCR[AsyncOperation[OCRResult]], ModelAsyncAttachMixin[AsyncOperation[OCRResult]]):
    _operation_type = AsyncOperation[OCRResult]

    async def run(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60,
    ) -> OCRResult:
        return await self._run(content, mime_type=mime_type, timeout=timeout)

    async def run_deferred(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncOperation[OCRResult]:
        return await self._run_deferred(content, mime_type=mime_type, timeout=timeout)


@doc_from(BaseOCR)
class OCR(BaseOCR[Operation[OCRResult]], ModelSyncAttachMixin[Operation[OCRResult]]):
    _operation_type = Operation[OCRResult]

    __run = run_sync(BaseOCR._run)
    __run_deferred = run_sync(BaseOCR._run_deferred)

    def run(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60,
    ) -> OCRResult:
        return self.__run(content, mime_type=mime_type, timeout=timeout)

    def run_deferred(
        self,
        content: bytes,
        *,
        mime_type: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60,
    ) -> Operation[OCRResult]:
        return self.__run_deferred(content, mime_type=mime_type, timeout=timeout)


OCRTypeT = TypeVar('OCRTypeT', bound=BaseOCR)
