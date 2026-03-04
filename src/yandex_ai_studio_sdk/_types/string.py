from __future__ import annotations

from collections.abc import Sequence
from typing import Union

from typing import TypeAlias

SmartStringSequence: TypeAlias = Union[str, Sequence[str]]


def coerce_string_sequence(value: SmartStringSequence) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value, )

    return tuple(value)
