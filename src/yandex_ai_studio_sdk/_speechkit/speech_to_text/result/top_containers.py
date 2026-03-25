# pylint: disable=no-name-in-module,invalid-enum-extension,protected-access
from __future__ import annotations

import warnings
from collections.abc import Generator, Iterable, Sequence
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, ClassVar, Optional, TypeVar, overload

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
from .classifier import ClassifierResult, ClassifierUpdate
from .context import RequestDetails
from .conversation_analysis import ConversationAnalysis
from .llm_post_process_result import LLMPostProcessResult
from .speaker_analysis import SpeakerAnalysis
from .status_code import StatusCode
from .utils import TimeSpan


class SpeechToTextStreamingEventType(str, Enum):
    """Type of speech to text streaming event"""

    partial = 'partial'
    final = 'final'
    eou_update = 'eou_update'
    final_refinement = 'final_refinement'
    status_code = 'status_code'
    classifier_update = 'classifier_update'
    speaker_analysis = 'speaker_analysis'
    conversation_analysis = 'conversation_analysis'
    llm_post_process_result = 'llm_post_process_result'
    #: In case of backend adding new fields
    sdk_unknown = 'sdk_unknown'

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass(frozen=True)
class BaseSpeechToTextResult(BaseResult):
    _sdk: SDKType = field(repr=False)

    #: Field role is required to be compatible with TextMessage Protocol, to
    #: other part of SDK could use this object an input.
    role: ClassVar[str] = 'user'

    #: Internal session identifier.
    uuid: str
    #: User session identifier.
    user_request_id: str
    #: Conversation statistics
    conversation_analysis: ConversationAnalysis | None
    #: Result of llm post_process, may be also known as `Summarization` at some old documentation.
    llm_post_process_result: LLMPostProcessResult | None



ChannelGenerator = Generator[None, Optional['SpeechToTextStreamingEvent'], 'ChannelResult']


@dataclass(frozen=True)
class Utterance:
    """A class representing result of speech recognition request for one utterance in
    specific audio channel.

    Boundaries of this utterance is determined by end of utterance classifier setting,
    silence duration between utterances or external ``stream.eou()`` calls

    """
    #: all events from this utterance for debugging purposes
    events: tuple[SpeechToTextStreamingEvent, ...] = field(repr=False)
    #: classifier results for this utterance
    classifiers: dict[str, ClassifierResult]
    #: speker analysis for this utterance
    speaker_analysis: SpeakerAnalysis | None

    #: Utterance time boundaries
    timespan: TimeSpan
    #: All final alternatives from this utterance
    finals: tuple[Alternatives, ...]
    #: All refined final alternatives from this utterance
    final_refinements: tuple[FinalRefinement, ...] | None

    @property
    def final_text(self) -> str:
        """Joined text of all final events in this utterance`"""
        return ' '.join(final.text or '' for final in self.finals)

    @property
    def final_refinement_text(self) -> str | None:
        """Joined text of all final_refinement events if there are any"""
        if not self.final_refinements:
            return None
        return ' '.join(final.text or '' for final in self.final_refinements)

    @property
    def text(self) -> str:
        """final_refinement_text or final_text"""
        return self.final_refinement_text or self.final_text

    @classmethod
    def _from_events_iterable(
        cls,
        *,
        events: Iterable[SpeechToTextStreamingEvent],
        sdk: SDKType,  # pylint: disable=unused-argument
    ):
        speaker_analysis: SpeakerAnalysis | None = None
        classifiers: dict[str, ClassifierResult] = {}
        finals: list[Alternatives] = []
        final_refinements: list[FinalRefinement] = []

        for event in events:
            match event.event_type:
                case SpeechToTextStreamingEventType.speaker_analysis:
                    speaker_analysis = event.speaker_analysis
                case SpeechToTextStreamingEventType.classifier_update \
                    if (
                        event.classifier_update and
                        event.classifier_update.window_type == ClassifierUpdate.WindowType.LAST_UTTERANCE
                    ):

                    classifier = event.classifier_update
                    classifiers[classifier.name] = ClassifierResult._from_classifier_update(classifier)
                case SpeechToTextStreamingEventType.final:
                    assert event.final
                    finals.append(event.final)
                case SpeechToTextStreamingEventType.final_refinement:
                    assert event.final_refinement
                    final_refinements.append(event.final_refinement)

        if not finals:
            raise ValueError('session have no events with event_type="final"')

        timespan = TimeSpan(
            start_time_ms=finals[0].timespan.start_time_ms,
            end_time_ms=finals[-1].timespan.end_time_ms,
        )
        return cls(
            events=tuple(events),
            speaker_analysis=speaker_analysis,
            classifiers=classifiers,
            finals=tuple(finals),
            final_refinements=tuple(final_refinements) if final_refinements else None,
            timespan=timespan,
        )


@dataclass(frozen=True)
class ChannelResult(Sequence):
    """A class representing result of speech recognition request for one audio channel
    """
    tag: str
    #: All utterances from this channel
    utterances: tuple[Utterance, ...]
    #: Speech statistics for this channel with window_type=TOTAL
    speaker_analysis: SpeakerAnalysis | None

    def __len__(self):
        return len(self.utterances)

    @overload
    def __getitem__(self, index: int, /) -> Utterance:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[Utterance, ...]:
        pass

    def __getitem__(self, index, /):
        return self.utterances[index]

    @property
    def final_text(self) -> str:
        """Joined text of all final events in this channel"""
        return ' '.join(utterance.final_text for utterance in self.utterances)

    @property
    def final_refinement_text(self) -> str | None:
        """Joined text of all final_refinement events if there are any"""
        not_null_refinements = [
            utterance.final_refinement_text
            for utterance in self.utterances
            if utterance.final_refinement_text
        ]
        if not not_null_refinements:
            return None
        return ' '.join(not_null_refinements)

    @property
    def text(self) -> str:
        """final_refinement_text or final_text"""
        return self.final_refinement_text or self.final_text

    @classmethod
    def _from_events_iterable(
        cls,
        *,
        events: Iterable[SpeechToTextStreamingEvent],
        sdk: SDKType,
    ) -> ChannelResult:
        utterances: list[Utterance] = []
        utterance_events: list[SpeechToTextStreamingEvent] = []
        eou = False
        speaker_analysis: SpeakerAnalysis | None = None
        tag: str | None = None

        def flush() -> None:
            nonlocal eou
            nonlocal utterance_events
            eou = False
            utterance = Utterance._from_events_iterable(
                events=utterance_events,
                sdk=sdk
            )
            utterance_events = []
            utterances.append(utterance)

        for event in events:
            tag = event.channel_tag
            # all events:
            # 1) Events, relevant to Utterance we are saving into local vars.
            # 2) All other events we are saving into utterance event list.
            # 3) after eou event we are starting to wait new partial/final event.
            # 4) after new partial/final we are creating Utterance object and clearing
            #    utterance event list.
            # 5) after all events we are creating Utterance object anyway with current
            #    utterance event list.
            match event.event_type:
                case SpeechToTextStreamingEventType.eou_update:
                    eou = True
                    utterance_events.append(event)
                case SpeechToTextStreamingEventType.speaker_analysis \
                    if (
                        event.speaker_analysis and
                        event.speaker_analysis.window_type == SpeakerAnalysis.WindowType.TOTAL
                    ):

                    speaker_analysis = event.speaker_analysis
                case (
                    SpeechToTextStreamingEventType.partial |
                    SpeechToTextStreamingEventType.final |
                    SpeechToTextStreamingEventType.final_refinement
                ):
                    if eou:
                        flush()
                    utterance_events.append(event)
                case _:
                    utterance_events.append(event)

        if utterance_events:
            flush()

        assert tag, "It is not None by design"
        return cls(
            tag=tag,
            utterances=tuple(utterances),
            speaker_analysis=speaker_analysis,
        )


@dataclass(frozen=True)
class SpeechToTextResult(BaseSpeechToTextResult, Sequence):
    """A class representing result of speech recognition request.

    Main thing it contains -- one or more channel results.
    In case of one channel, you could use a proxy-properties to access channel result.

    Lets assume we have a some speech to text result.
    It doesn't matter how I creating it in this example, but I need to do it for doctesting
    purposes.

    >>> first_result = ChannelResult(utterances=(), speaker_analysis=None, tag="222_first")
    >>> result = SpeechToTextResult(
    ...    _sdk=None,
    ...    uuid='123',
    ...    user_request_id='234',
    ...    conversation_analysis=None,
    ...    llm_post_process_result=None,
    ...    unknown_events=(),
    ...    status_events=(),
    ...    channels={
    ...        '222_first': first_result,
    ...    }
    ... )

    Example of proxy-properties:

    >>> text = result.text
    >>> final_text = result.text

    Let's add another channel result:

    >>> second_result = ChannelResult(utterances=(), speaker_analysis=1, tag="111_second")
    >>> result.channels['111_second'] = second_result

    >>> text = result.text
    Traceback (most recent call last):
        ...
    ValueError: property proxy ... is not available in case of 2+ channels in result

    And here is example for how to access channel results from result:

    We can get it by channel tag:

    >>> assert result['222_first'] == result.channels['222_first'] is first_result

    We can access it by channel "index" which we calculate based on alphabetical sorting
    of channel tags
    (catch is, usually tags is match indices i.e. when tag=='0', corresponding index will be
    also 0, but in this example I intentionally put reversed tags):

    >>> assert result[0] == result.get_channel(0) is second_result
    >>> assert result[-1] == result.get_channel(-1) is first_result

    Also you can use slices:

    >>> assert result[0:2] == (second_result, first_result)

    And you could iterate over channels:

    >>> assert list(result) == [second_result, first_result]
    """

    unknown_events: tuple[SpeechToTextStreamingEvent, ...] = field(repr=False)
    status_events: tuple[SpeechToTextStreamingEvent, ...] = field(repr=False)
    channels: dict[str, ChannelResult]

    def get_channel(self, sequential_number: int) -> ChannelResult:
        """Get channel by it's sequential number among all channels, sorted by its tags"""
        assert self.channels
        channel_tag = sorted(self.channels)[sequential_number]
        return self.channels[channel_tag]

    def _force_single_channel(self) -> None:
        if len(self.channels) > 1:
            raise ValueError(
                'property proxy from SpeechToTextResult to ChannelResult is not available '
                'in case of 2+ channels in result'
            )

    @property
    def final_text(self) -> str:
        """Return final text of first channel.

        Raises if result have more than one channel.
        """

        self._force_single_channel()
        return self.get_channel(0).final_text

    @property
    def final_refinement_text(self) -> str | None:
        """Return final text of first channel.

        Raises if result have more than one channel.
        """
        self._force_single_channel()
        return self.get_channel(0).final_refinement_text

    @property
    def text(self) -> str:
        """Return final text of first channel.

        Raises if result have more than one channel.
        """
        self._force_single_channel()
        return self.get_channel(0).text

    @property
    def speaker_analysis(self) -> SpeakerAnalysis | None:
        """Return speaker_analysis for the first channel.

        Raises if result have more than one channel.
        """
        self._force_single_channel()
        return self.get_channel(0).speaker_analysis

    def __len__(self):
        return len(self.channels)

    @overload
    def __getitem__(self, index: int | str, /) -> ChannelResult:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[ChannelResult, ...]:
        pass

    def __getitem__(self, index, /):
        if isinstance(index, str):
            return self.channels[index]
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            return tuple(self.get_channel(i) for i in range(start, stop, step))

        return self.get_channel(index)

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[StreamingResponse],
        sdk: SDKType,
        ctx: RequestDetails,
    ) -> Self:
        events = (SpeechToTextStreamingEvent._from_proto(proto=p, sdk=sdk, ctx=ctx) for p in proto)
        uuid: str | None = None
        user_request_id: str | None = None

        unknown_events: list[SpeechToTextStreamingEvent] = []
        status_events: list[SpeechToTextStreamingEvent] = []
        channels_events: dict[str, list[SpeechToTextStreamingEvent]] = {}
        conversation_analysis: ConversationAnalysis | None = None
        llm_post_process_result: LLMPostProcessResult | None = None

        for event in events:
            uuid = uuid or event.uuid
            user_request_id = user_request_id or event.user_request_id

            match event.event_type:
                case SpeechToTextStreamingEventType.sdk_unknown:
                    unknown_events.append(event)
                case SpeechToTextStreamingEventType.status_code:
                    status_events.append(event)
                case SpeechToTextStreamingEventType.conversation_analysis:
                    conversation_analysis = event.conversation_analysis
                case SpeechToTextStreamingEventType.llm_post_process_result:
                    llm_post_process_result = event.llm_post_process_result
                case _ if event.channel_tag:
                    channels_events.setdefault(event.channel_tag, []).append(event)
                case _:
                    warnings.warn(
                        f"got unclassified event {event} with empty channel tag, "
                        "please update SDK and if this message persists, contact the "
                        "support",
                        UserWarning,
                    )

        if not uuid:
            raise RuntimeError(
                'missing any event with uuid in session or empty deferred answer'
            )
        assert user_request_id

        channels = {
            channel_tag: ChannelResult._from_events_iterable(
                sdk=sdk,
                events=events,
            ) for channel_tag, events in channels_events.items()
        }

        return cls(
            _sdk=sdk,
            uuid=uuid,
            user_request_id=user_request_id,
            status_events=tuple(status_events),
            unknown_events=tuple(unknown_events),
            channels=channels,
            conversation_analysis=conversation_analysis,
            llm_post_process_result=llm_post_process_result,
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
        kwargs = {}
        for field_ in fields(raw_result):
            kwargs[field_.name] = getattr(raw_result, field_.name)
        return cls(
            operation_id=operation_id,
            **kwargs,
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
    BaseSpeechToTextResult,
    BaseProtoModelResult[StreamingResponse, RequestDetails],
):
    """A class representing streaming event of speech recognition request."""

    #: str/enum representation of event type
    event_type: SpeechToTextStreamingEventType
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

        kwargs: dict[str, Any] = {
            'conversation_analysis': None,
            'llm_post_process_result': None,
        }

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
                    # this is really should never happen, because we control
                    # SpeechToTextStreamingEventType enum
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
