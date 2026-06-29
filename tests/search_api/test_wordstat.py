from __future__ import annotations

import datetime

import pytest

from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._search_api.types import Region


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_wordstat_get_top(async_sdk: AsyncAIStudio) -> None:
    wordstat = async_sdk.search_api.wordstat()
    result = await wordstat.get_top(
        'yandex cloud',
        num_phrases=10,
        regions=["225", Region(id="1", label="2", children=None)],
        devices=['phone', wordstat.DeviceType.DESKTOP],
    )
    assert len(result.associations) >= 1
    assert len(result.results) >= 1


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_wordstat_get_dynamics(async_sdk: AsyncAIStudio) -> None:
    wordstat = async_sdk.search_api.wordstat()
    result = await wordstat.get_dynamics(
        'yandex cloud',
        from_date=datetime.date(2026, 5, 1),
        to_date=datetime.date(2026, 5, 2),
        regions=["225", Region(id="1", label="2", children=None)],
        devices=['phone', wordstat.DeviceType.DESKTOP],
        period='daily',
    )
    assert len(result) == 2

    assert result[0].date == datetime.date(2026, 5, 1)


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_wordstat_get_regions_tree(async_sdk: AsyncAIStudio) -> None:
    wordstat = async_sdk.search_api.wordstat()
    result = await wordstat.get_regions_tree()
    assert len(result) > 5
    assert len(list(result.dfs())) > 100
    regions = result.search_by_label('Пушкинский район')
    assert regions
    assert regions[0].id == '98604'


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_wordstat_get_regions_distribution(async_sdk: AsyncAIStudio) -> None:
    wordstat = async_sdk.search_api.wordstat()
    result = await wordstat.get_regions_distribution(
        "yandex cloud"
    )
    assert len(result) > 1
    assert not result[0].region

    result = await wordstat.get_regions_distribution(
        "yandex cloud",
        resolve_regions=True,
        devices=['phone', wordstat.DeviceType.DESKTOP],
        distribution_type=wordstat.RegionsDistributionType.CITIES,
    )

    assert len(result) > 1
    assert result[0].region
