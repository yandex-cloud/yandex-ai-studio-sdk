# pylint: disable=no-name-in-module,invalid-enum-extension
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, TypeVar

from google.protobuf.empty_pb2 import Empty
from typing_extensions import Self, override
from yandex.cloud.ai.stt.v3.stt_pb2 import DeleteRecognitionRequest, StreamingResponse
from yandex.cloud.ai.stt.v3.stt_service_pb2_grpc import AsyncRecognizerStub

from yandex_ai_studio_sdk._types.proto import ProtoBased
from yandex_ai_studio_sdk._types.result import BaseProtoModelResult, BaseResult, SDKType
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .alternatives import Alternatives, FinalRefinement
from .audio_cursors import AudioCursors
from .classifier import ClassifierUpdate
from .context import RequestDetails
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
class SpeechToTextResult(BaseResult):
    """A class representing result of speech recognition request.
    """

    _sdk: SDKType = field(repr=False)

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        sdk: SDKType,
        ctx: RequestDetails,
    ) -> Self:
        events = [SpeechToTextStreamingEvent._from_proto(proto=p, sdk=sdk, ctx=ctx) for p in proto]
        print(events)
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

    @classmethod
    def _from_proto_iterable_operation(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        sdk: SDKType,
        ctx: RequestDetails,
        operation_id: str,
    ) -> Self:
        raw_result = SpeechToTextResult._from_proto_iterable(proto=proto, sdk=sdk, ctx=ctx)
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
    BaseProtoModelResult[StreamingResponse, RequestDetails],
):
    """A class representing streaming event of speech recognition request."""

    _sdk: SDKType = field(repr=False)

    #: Field role is required to be compatible with TextMessage Protocol, to
    #: other part of SDK could use this object an input.
    role: ClassVar[str] = 'user'

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

    @property
    def final_text(self) -> str | None:
        """Helper for ``result.final.text if result.final else None``"""
        return self.final.text if self.final else None

    @property
    def final_refinement_text(self) -> str | None:
        """Helper for ``result.final_refinement.text if result.final_refinement else None``"""
        return self.final_refinement.text if self.final_refinement else None

    @property
    def partial_text(self) -> str | None:
        """Helper for ``result.partial.text if result.partial else None``"""
        return self.partial.text if self.partial else None

    @property
    def text(self) -> str | None:
        """Helper for getting refined, final or partial text if event have any"""
        return self.final_refinement_text or self.final_text or self.partial_text

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    def _from_proto(cls, *, proto: StreamingResponse, sdk: SDKType, ctx: RequestDetails) -> Self:
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
