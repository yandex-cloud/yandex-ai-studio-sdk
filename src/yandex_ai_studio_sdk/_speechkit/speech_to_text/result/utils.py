from __future__ import annotations

from dataclasses import dataclass, fields


class NotNoneReprMixin:
    def __repr__(self):
        cls = type(self).__name__
        field_strings = []
        for f in fields(self):
            if f.name == '_sdk':
                continue
            value = getattr(self, f.name)
            if value is not None:
                field_strings.append(f"{f.name}={value!r}")
        return f"{cls}({', '.join(field_strings)})"



@dataclass(frozen=True)
class TimeSpan:
    #: Audio segment start time.
    start_time_ms: int

    #: Audio segment end time.
    end_time_ms: int

    def __repr__(self) -> str:
        return f'[{self.start_time_ms}-{self.end_time_ms}]ms'
