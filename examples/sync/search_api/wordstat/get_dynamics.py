#!/usr/bin/env python3

from __future__ import annotations

import pprint
from datetime import date, timedelta

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

    today = date.today()
    to_date = today - timedelta(days=10)
    from_date = to_date - timedelta(days=5)

    dynamics = wordstat.get_dynamics(
        search_query,
        'daily',
        from_date=from_date,
        to_date=to_date,
        # more on how to use devices and regions look at get_top.py
        devices=['desktop'],
        regions=['225'],
    )
    print(
        f"Number of quieries from {from_date.strftime(DATE_FORMAT)} to {to_date.strftime(DATE_FORMAT)} "
        "in Russia from desktop:"
    )
    # Printing result object to see a structure:
    pprint.pprint(dynamics)

    to_date = today.replace(day=1) - timedelta(days=1) # end of the previous month
    month = today.month - 6
    if month <= 0:
        year = today.year - 1
        month += 12
    else:
        year = today.year

    month = month % 12 or 12
    from_date = date(year, month, 1) # start of the month 6 months ago

    dynamics = wordstat.get_dynamics(
        search_query,
        wordstat.PeriodType.MONTHLY,
        from_date=from_date,
        to_date=to_date,
    )

    print(f"Result from {from_date.strftime(DATE_FORMAT)} to {to_date.strftime(DATE_FORMAT)} by months:")
    print("Month".ljust(11) + " | " + "Count".rjust(10) + " | " + "Share".rjust(10))
    for item in dynamics:
        print(f"{item.date.strftime(DATE_FORMAT):>11} | {item.count:>10} | {item.share:10.6%}")


if __name__ == '__main__':
    main()
