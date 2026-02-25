from __future__ import annotations

from .json import JsonBased
from .proto import ProtoBased, ProtoBasedWithCtx, ProtoMessage, ProtoMessageTypeT, SDKType
from .request import RequestDetailsTypeT

# it is left here until further refactoring
__all__ = ['ProtoMessage', 'BaseProtoResult', 'SDKType', 'BaseResult', 'BaseJsonResult']


class BaseResult:
    pass


class BaseProtoResult(BaseResult, ProtoBased[ProtoMessageTypeT]):
    pass


class BaseProtoModelResult(
    BaseResult,
    ProtoBasedWithCtx[ProtoMessageTypeT, RequestDetailsTypeT],
):
    pass

class BaseJsonResult(BaseResult, JsonBased):
    pass
