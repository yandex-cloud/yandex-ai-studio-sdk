from __future__ import annotations

from .config import DeviceType as DeviceType_
from .config import PeriodType as PeriodType_
from .config import RegionsDistributionType as RegionsDistributionType_


class SynonymsMixin:
    #: Link to :py:class:`yandex_ai_studio_sdk._search_api.wordstat.config.DeviceType`
    #: for more convenient access
    DeviceType = DeviceType_

    #: Link to :py:class:`yandex_ai_studio_sdk._search_api.wordstat.config.PeriodType`
    #: for more convenient access
    PeriodType = PeriodType_

    #: Link to :py:class:`yandex_ai_studio_sdk._search_api.wordstat.config.RegionsDistributionType`
    #: for more convenient access
    RegionsDistributionType = RegionsDistributionType_
