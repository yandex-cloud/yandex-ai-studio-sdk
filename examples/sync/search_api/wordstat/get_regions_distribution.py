#!/usr/bin/env python3

from __future__ import annotations

import operator
import pprint

from yandex_ai_studio_sdk import AIStudio

DATE_FORMAT = "%Y-%m-%d"


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    wordstat = sdk.search_api.wordstat()

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    regions_distribution_resolved = wordstat.get_regions_distribution(
        search_query,
        # NB: resolve_regions=True is making extra request to get_regions_tree method
        resolve_regions=True,
        distribution_type='cities'
    )
    regions_distribution_unresolved = wordstat.get_regions_distribution(
        search_query,
        distribution_type='all'
    )

    # just an item with region_id you have to resolve by yourself:
    print("region item with resolve_regions=False (default):")
    pprint.pprint(regions_distribution_unresolved[0])

    # now item of result have field "region", which contains not only region name,
    # but also info about this region children regions:
    print("region item with resolve_regions=True:")
    pprint.pprint(regions_distribution_resolved[0])

    regions_distribution = wordstat.get_regions_distribution(
        search_query,
        resolve_regions=True,
        distribution_type=wordstat.RegionsDistributionType.REGIONS,
        devices=['tablet', wordstat.DeviceType.DESKTOP]
    )
    print()
    heading = (
        "Region name".rjust(50) + " | " +
        "Count".rjust(10) + " | " +
        "Share".rjust(10) + " | " +
        "Affinity index".rjust(15)
    )
    print(heading)
    print('-' * len(heading))
    for item in sorted(
        regions_distribution,
        key=operator.attrgetter('count'),
        reverse=True
    )[:30]:
        assert item.region
        print(f"{item.region.label:>50} | {item.count:>10} | {item.share:10.6%} | {item.affinity_index:15.3f}")


if __name__ == '__main__':
    main()
