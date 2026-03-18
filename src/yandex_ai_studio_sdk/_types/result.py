from __future__ import annotations

from typing import TypeVar

from .json import JsonBased
from .proto import ContextTypeT, ProtoBased, ProtoBasedWithCtx, ProtoMessage, ProtoMessageTypeT, SDKType

# it is left here until further refactoring
__all__ = ['ProtoMessage', 'BaseProtoResult', 'SDKType', 'BaseResult', 'BaseJsonResult']


class BaseResult:
    pass


class BaseProtoResult(BaseResult, ProtoBased[ProtoMessageTypeT]):
    pass


class BaseProtoModelResult(
    BaseResult,
    ProtoBasedWithCtx[ProtoMessageTypeT, ContextTypeT],
):
    pass

class BaseJsonResult(BaseResult, JsonBased):
    pass


ProtoModelResultTypeT = TypeVar('ProtoModelResultTypeT', bound=BaseProtoModelResult)
