from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True, eq=True)
class TimeSpan:
    #: Audio segment start time.
    start_time_ms: int

    #: Audio segment end time.
    end_time_ms: int

    @property
    def length_ms(self) -> int:
        """Return length of given time span in milliseconds"""
        return self.end_time_ms - self.start_time_ms

    def __repr__(self) -> str:
        return f'[{self.start_time_ms}-{self.end_time_ms}]ms'
