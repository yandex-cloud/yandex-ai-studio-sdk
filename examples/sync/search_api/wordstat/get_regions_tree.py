#!/usr/bin/env python3

from __future__ import annotations

import pprint

from yandex_ai_studio_sdk import AIStudio


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

    region_tree = wordstat.get_regions_tree()
    # tree is very big to print it to terminal
    number_of_regions = sum(1 for _ in region_tree.dfs())
    print(f'Total of {number_of_regions} regions loaded')

    # there could be several regions with the same name, so by default we are returning tuple of values:
    pprint.pprint(region_tree.search_by_label('Пушкинский район'))

    # in case if you sure there is only one region with the name, you could pass first=True value
    # to get Region object instead of the tuple
    spb = region_tree.search_by_label('Санкт-Петербург и Ленинградская область', first=True)
    assert spb
    print(f"Saint-Petersburg region_id={spb.id}")

    # NB: search by label is using DFS inside to not allocate additional memory;
    # Also it is not doing any normalization.
    # So if you need something more intelligent, feel free to use region_tree.dfs() for
    # doing custom search
    region_with_complex_name = region_tree.search_by_label('Кот-д’Ивуар')
    assert region_with_complex_name
    print(f"Ivory coast: {region_with_complex_name}")


if __name__ == '__main__':
    main()
