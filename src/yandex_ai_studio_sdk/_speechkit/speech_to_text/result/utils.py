from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeSpan:
    #: Audio segment start time.
    start_time_ms: int

    #: Audio segment end time.
    end_time_ms: int

    def __repr__(self) -> str:
        return f'[{self.start_time_ms}-{self.end_time_ms}]ms'
