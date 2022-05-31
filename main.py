from gevent import monkey
monkey.patch_all(thread=False, select=False)  # necessary as first code executed for grequests
from typing import List
import pandas as pd

import scrape_sales_data


def main(suburbs: List[str], state: str) -> pd.DataFrame:
    urls = scrape_sales_data.build_urls_for_suburbs(suburbs, state)
    df = scrape_sales_data.get_all_sales_data_from_urls(urls)
    return df


if __name__ == '__main__':
    state = 'WA'
    suburbs = [
        'Scarborough',
        'Wembley Downs',
        'Doubleview'
    ]

    df = main(suburbs, state)
