from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .model_config import ConfigTypeT
from .proto import Context


@dataclass(frozen=True)
class RequestDetails(Context, Generic[ConfigTypeT]):
    """:meta private:

    Object that encapsulates a model request in a result
    to enable result methods which require context"""

    model_config: ConfigTypeT
    timeout: float


RequestDetailsTypeT = TypeVar('RequestDetailsTypeT', bound=RequestDetails)
