# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass

from yandex.cloud.ai.stt.v3.stt_pb2 import AudioCursors as ProtoAudioCursors

from yandex_ai_studio_sdk._types.proto import ProtoMirrored


@dataclass(frozen=True)
class AudioCursors(ProtoMirrored[ProtoAudioCursors]):
    #: Number of audio chunks received by the server. This cursor is moved after each audio chunk is received by the server.
    received_data_ms: int

    #: Input stream reset data.
    reset_time_ms: int

    #: How much audio was processed. This time includes trimming silences as well.
    #: This cursor is moved after the server receives enough data to update recognition results (includes silence as well).
    partial_time_ms: int

    #: Time of last final.
    #: This cursor is moved when server decides that recognition from start of audio until
    #: `final_time_ms` will not change anymore.
    #: Usually this event is followed by EOU detection. This behavior could change in future.
    final_time_ms: int

    #: This is the index of the last final result sent by the server. Incremented after each new final.
    final_index: int

    #: Estimated time of EOU. Cursor is updated after each new EOU is sent.
    #: For external classifier this equals [received_data_ms] at the moment EOU event arrives.
    #: For internal classifier this is an estimate of the time.
    #: The time is not exact and has the same guarantees as word timings.
    eou_time_ms: int
