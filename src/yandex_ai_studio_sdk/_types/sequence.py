from __future__ import annotations

import abc
from collections.abc import Iterator, Sequence
from typing import Generic, TypeVar, overload

from typing_extensions import override

T = TypeVar('T')


class TupleSequence(abc.ABC, Sequence[T], Generic[T]):
    """Mixin that implements the full ``Sequence[T]`` interface by delegating
    to an abstract ``_items`` property backed by a ``tuple[T, ...]``.

    Subclasses only need to implement ``_items``; typically this is a one-liner
    that returns the relevant dataclass field::

        @property
        def _items(self) -> tuple[Word, ...]:
            return self.words
    """

    @property
    @abc.abstractmethod
    def _items(self) -> tuple[T, ...]: ...

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> tuple[T, ...]: ...

    @override
    def __getitem__(self, index: int | slice) -> T | tuple[T, ...]:
        return self._items[index]

    @override
    def __len__(self) -> int:
        return len(self._items)

    @override
    def __iter__(self) -> Iterator[T]:
        return iter(self._items)
