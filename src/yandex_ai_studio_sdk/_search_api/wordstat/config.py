from __future__ import annotations

from dataclasses import dataclass

from yandex.cloud.searchapi.v2.wordstat_service_pb2 import Device as ProtoDevice
from yandex.cloud.searchapi.v2.wordstat_service_pb2 import GetDynamicsRequest

from yandex_ai_studio_sdk._types.enum import ProtoBasedEnum
from yandex_ai_studio_sdk._types.model_config import BaseModelConfig


class Device(ProtoBasedEnum):
    """Device type"""

    __proto_enum_type__ = ProtoDevice
    __common_prefix__ = 'DEVICE_'

    ALL = ProtoDevice.DEVICE_ALL
    DESKTOP = ProtoDevice.DEVICE_DESKTOP
    PHONE = ProtoDevice.DEVICE_PHONE
    TABLET = ProtoDevice.DEVICE_TABLET


class PeriodType(ProtoBasedEnum):
    """Requested period type"""

    __proto_enum_type__ = GetDynamicsRequest.Period
    __common_prefix__ = 'PERIOD_'

    MONTHLY = GetDynamicsRequest.Period.PERIOD_MONTHLY
    WEEKLY = GetDynamicsRequest.Period.PERIOD_WEEKLY
    DAILY = GetDynamicsRequest.Period.PERIOD_DAILY


@dataclass(frozen=True)
class WordstatConfig(BaseModelConfig):
    pass
