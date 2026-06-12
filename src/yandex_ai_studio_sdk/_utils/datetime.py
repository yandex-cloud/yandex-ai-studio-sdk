from __future__ import annotations

from datetime import date, datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp


def to_timestamp(value: datetime | date | float | int) -> Timestamp:
    if isinstance(value, (float, int)):
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
    elif isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    else:
        dt = datetime(value.year, value.month, value.day, tzinfo=timezone.utc)

    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts
