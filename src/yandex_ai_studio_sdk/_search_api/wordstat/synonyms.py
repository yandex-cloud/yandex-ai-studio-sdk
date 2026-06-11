from __future__ import annotations

from .config import Device as Device_
from .config import PeriodType as PeriodType_


class SynonymsMixin:
    #: Link to :py:class:`yandex_ai_studio_sdk._search_api.wordstat.config.Device`
    #: for more convenient access
    Device = Device_

    #: Link to :py:class:`yandex_ai_studio_sdk._search_api.wordstat.config.PeriodType`
    #: for more convenient access
    PeriodType = PeriodType_
