#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pprint

from yandex_ai_studio_sdk import AsyncAIStudio


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    wordstat = sdk.search_api.wordstat()

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    top = await wordstat.get_top(search_query, 1)
    if not top.results:
        print('nothing found')
        return

    number = list(top.results.values())[0]
    print(f"Number requests for {search_query}: {number}")

    top = await wordstat.get_top(search_query, 50)
    print(f"Top requests ({len(top.results)}):")
    # .results and .associations contains a dict-like object with stats:
    for request, number in top.results.items():
        print(f" - {request}: {number}")

    print(f"Top associations ({len(top.associations)}):")
    pprint.pprint(dict(top.associations))

    # for details about regions tree refer to get_regions_tree.py example file
    region_tree = await wordstat.get_regions_tree()
    msk = region_tree.search_by_label("Москва")
    spb = region_tree.search_by_label("Санкт-Петербург")
    # we need to check if search_by_label returned something
    assert msk and spb

    # now I showing get_top request with additional filters:
    top = await wordstat.get_top(
        request,
        num_phrases=1,
        regions=msk + spb,
        # you can specify devices values with two different ways
        devices=['tablet', wordstat.DeviceType.PHONE]
    )
    if not top.results:
        print("nothing found for MSK and SPB for mobile devices")
        return
    number = list(top.results.values())[0]
    print(f"Number requests for {search_query} in Moscow from portable devices: {number}")


if __name__ == '__main__':
    asyncio.run(main())
