# pylint: disable=no-name-in-module,invalid-enum-extension,unused-argument
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import override
from yandex.cloud.ai.stt.v3.stt_pb2 import DescriptiveStatistics as ProtoDescriptiveStatistics
from yandex_ai_studio_sdk._types.proto import ProtoMirrored, SDKType


@dataclass(frozen=True)
class DescriptiveStatistics(ProtoMirrored[ProtoDescriptiveStatistics]):
    #: Minimum observed value.
    min: float

    #: Maximum observed value.
    max: float

    #: Estimated mean of distribution.
    mean: float

    #: Estimated standard deviation of distribution.
    std: float

    #: List of evaluated quantiles.
    quantiles: dict[float, float]

    @override
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoDescriptiveStatistics, sdk: SDKType) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)
        kwargs['quantiles'] = {
            quantile.level: quantile.value
            for quantile in proto.quantiles
        }
        for key, value in kwargs.items():
            if value == 'Infinity':
                kwargs[key] = float('inf')
        return kwargs
