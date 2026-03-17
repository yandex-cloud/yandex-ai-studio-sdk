# pylint: disable=no-name-in-module,invalid-enum-extension
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from google.protobuf.empty_pb2 import Empty
from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import DeleteRecognitionRequest, StreamingResponse
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import AsyncRecognizerStub
from yandex_ai_studio_sdk._speechkit.speech_to_text.config import SpeechToTextConfig
from yandex_ai_studio_sdk._types.proto import ProtoBased
from yandex_ai_studio_sdk._types.request import RequestDetails
from yandex_ai_studio_sdk._types.result import BaseProtoModelResult, BaseProtoResult, SDKType
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .alternatives import Alternatives, FinalRefinement
from .audio_cursors import AudioCursors
from .classifier import ClassifierUpdate
from .conversation_analysis import ConversationAnalysis
from .llm_post_process_result import LLMPostProcessResult
from .speaker_analysis import SpeakerAnalysis
from .status_code import StatusCode


class SpeechToTextStreamingEventType(str, Enum):
    """Type of speech to text streaming event"""

    partial = 'partial'
    final = 'final'
    eou_update = 'eou_update'
    final_refinement = 'final_refinement'
    status_code = 'status_code'
    #: Result of the triggered classifier.
    classifier_update = 'classifier_update'
    #: Speech statistics for every speaker.
    speaker_analysis = 'speaker_analysis'
    #: Conversation statistics.
    conversation_analysis = 'conversation_analysis'
    #: Result of llm post processing
    llm_post_process_result = 'llm_post_process_result'
    #: In case of backend adding new fields
    sdk_unknown = 'sdk_unknown'

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass(frozen=True)
class SpeechToTextResult(BaseProtoResult[StreamingResponse]):
    """A class representing result of speech recognition request.
    """

    _sdk: SDKType = field(repr=False)

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    def _from_proto(cls, *, proto: StreamingResponse, sdk: SDKType) -> Self:
        print(proto)
        return cls(
            _sdk=sdk,
        )

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        sdk: SDKType,
    ) -> Self:
        print(proto)
        return cls(
            _sdk=sdk,
        )


@dataclass(frozen=True)
class DeferredSpeechToTextBaseResult(SpeechToTextResult):
    operation_id: str

    async def _delete(self, timeout: float = 60) -> None:
        """Deletes results of asynchronous recognition."""

        request = DeleteRecognitionRequest(operation_id=self.operation_id)
        async with self._sdk._client.get_service_stub(AsyncRecognizerStub, timeout=timeout) as stub:
            await self._sdk._client.call_service(
                stub.DeleteRecognition,
                request,
                timeout=timeout,
                expected_type=Empty
            )

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    def _from_proto(
        cls,
        *,
        proto: StreamingResponse,
        sdk: SDKType,
        operation_id: str | None = None
    ) -> Self:
        assert operation_id
        raw_result = SpeechToTextResult._from_proto(proto=proto, sdk=sdk)

        return cls(
            operation_id=operation_id,
            _sdk=raw_result._sdk,
        )

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        sdk: SDKType,
        operation_id: str | None = None
    ) -> Self:
        assert operation_id
        raw_result = SpeechToTextResult._from_proto_iterable(proto=proto, sdk=sdk)
        return cls(
            operation_id=operation_id,
            _sdk=raw_result._sdk,
        )


class AsyncDeferredSpeechToTextResult(DeferredSpeechToTextBaseResult):
    @doc_from(DeferredSpeechToTextBaseResult._delete)
    async def delete(self, timeout: float = 60) -> None:
        await self._delete(timeout=timeout)


class DeferredSpeechToTextResult(DeferredSpeechToTextBaseResult):
    __delete = run_sync(DeferredSpeechToTextBaseResult._delete)

    @doc_from(DeferredSpeechToTextBaseResult._delete)
    def delete(self, timeout: float = 60) -> None:
        self.__delete(timeout=timeout)


@dataclass(frozen=True)
# pylint: disable=too-many-instance-attributes
class SpeechToTextStreamingEvent(
    BaseProtoModelResult[StreamingResponse, RequestDetails[SpeechToTextConfig]],
):
    """A class representing streaming event of speech recognition request."""

    _sdk: SDKType = field(repr=False)

    #: str/enum representation of event type
    event_type: SpeechToTextStreamingEventType
    #: Internal session identifier.
    uuid: str
    #: User session identifier.
    user_request_id: str
    #: Wall clock on server side. This is time when server wrote results to stream.
    response_wall_time_ms: int
    #: Progress bar for stream session recognition: how many data we obtained; final and partial times; etc
    audio_cursors: AudioCursors
    #: Tag for distinguish audio channels.
    channel_tag: str

    #: Partial results, server will send them regularly after enough audio data was received from user.
    #: This is the current text estimation from `final_time_ms` to `partial_time_ms`.
    #: Could change after new data will arrive.
    partial: Alternatives | None = None
    #: Final results, the recognition is now fixed until `final_time_ms`.
    #: For now, final is sent only if the EOU event was triggered. This behavior could be changed in future releases.
    final: Alternatives | None = None
    #: For each final, if normalization is enabled, sent the normalized text (or some other advanced post-processing).
    #: Final normalization will introduce additional latency.
    final_refinement: FinalRefinement | None = None

    #: After EOU classifier, send the message with final, send the EouUpdate with time of EOU
    #: before eou_update we send final with the same time. there could be several finals before eou update.
    #: EOU estimated time.
    eou_update_ms: float | None = None

    #: Status messages, send by server with fixed interval (keep-alive).
    status_code: StatusCode | None = None

    #: Update on result of the triggered classifier.
    classifier_update: ClassifierUpdate | None = None

    #: Speech statistics for every speaker
    speaker_analysis: SpeakerAnalysis | None = None

    #: Conversation statistics
    conversation_analysis: ConversationAnalysis | None = None

    #: Result of llm post_process, may be also known as `Summarization` at some old documentation.
    llm_post_process_result: LLMPostProcessResult | None = None

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    def _from_proto(cls, *, proto: StreamingResponse, sdk: SDKType, ctx: RequestDetails[SpeechToTextConfig]) -> Self:
        value: Any = None
        event_type: SpeechToTextStreamingEventType

        for event_type in SpeechToTextStreamingEventType:
            if event_type == SpeechToTextStreamingEventType.sdk_unknown:
                continue
            field_name = {
                'llm_post_process_result': 'summarization'
            }.get(event_type.value, event_type.value)
            if proto.HasField(field_name):
                value = getattr(proto, field_name)
                break
        else:
            event_type = SpeechToTextStreamingEventType.sdk_unknown

        kwargs: dict[str, Any] = {}

        new_field_name = event_type.name
        parser_class: type[ProtoBased] | None

        #somewhy mypy thinks it must be ABCMeta
        parser_class = {  # type: ignore[assignment]
            SpeechToTextStreamingEventType.partial: Alternatives,
            SpeechToTextStreamingEventType.final: Alternatives,
            SpeechToTextStreamingEventType.final_refinement: FinalRefinement,
            SpeechToTextStreamingEventType.status_code: StatusCode,
            SpeechToTextStreamingEventType.classifier_update: ClassifierUpdate,
            SpeechToTextStreamingEventType.speaker_analysis: SpeakerAnalysis,
            SpeechToTextStreamingEventType.conversation_analysis: ConversationAnalysis,
        }.get(event_type)

        if parser_class:
            kwargs[new_field_name] = parser_class._from_proto(proto=value, sdk=sdk)
        else:
            new_value: Any = None
            match event_type:
                case SpeechToTextStreamingEventType.eou_update:
                    new_field_name = 'eou_update_ms'
                    new_value = value.time_ms
                case SpeechToTextStreamingEventType.llm_post_process_result:
                    new_field_name = 'llm_post_process_result'
                    new_value = LLMPostProcessResult._from_proto(
                        proto=value,
                        sdk=sdk,
                        ctx=ctx
                    )
                case SpeechToTextStreamingEventType.sdk_unknown:
                    pass
                case _:
                    assert False, "This should never happen"

            if new_value:
                kwargs[new_field_name] = new_value

        return cls(
            _sdk=sdk,
            audio_cursors=AudioCursors._from_proto(proto=proto.audio_cursors, sdk=sdk),
            event_type=event_type,
            uuid=proto.session_uuid.uuid,
            user_request_id=proto.session_uuid.uuid,
            response_wall_time_ms=proto.response_wall_time_ms,
            channel_tag=proto.channel_tag,
            **kwargs,
        )


DeferredSpeechToTextResultTypeT = TypeVar(
    'DeferredSpeechToTextResultTypeT',
    bound=DeferredSpeechToTextBaseResult
)
