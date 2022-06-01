import grequests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, parse_qs
import pandas as pd
import http
from typing import Generator, List
from tabulate import tabulate

from PropertySale import PropertySale


URL = 'http://house.speakingsame.com/p.php'
MAX_PAGES = 30  # max historical pages given by site


def get_search_params(suburb: str, state: str, page_num: int) -> dict:
    return {
        'q': suburb,
        'sta': state.lower(),
        'p': page_num,
        's': 1,
        'count': 9999999999
    }


def build_urls_for_suburbs(suburbs: List[str], state: str) -> Generator:
    if isinstance(suburbs, str):
        suburbs = [suburbs]
    return (f'{URL}?{urlencode(get_search_params(suburb, state, page_num))}'
            for suburb in suburbs
            for page_num in range(MAX_PAGES))


def get_all_sales_data_from_urls(urls: Generator) -> pd.DataFrame:
    unsent_requests = (grequests.get(url) for url in urls)
    responses = grequests.map(unsent_requests)

    all_sales = []
    failed_responses = []
    for response in responses:
        if response.status_code == http.HTTPStatus.OK:
            query_params = {k: v[0] for k, v in parse_qs(urlparse(response.url).query).items()}
            suburb = query_params['q']
            state = query_params['sta'].upper()
            soup = BeautifulSoup(response.text, features='html.parser')
            results = soup.select_one('#mainT > tr > td:nth-of-type(2) > div')
            if results is None:
                continue
            items = [itm for itm in results.find_all('table', recursive=False) if itm.attrs.get('id') != 'filter']
            sales = [PropertySale(item, suburb, state) for item in items]
            for sale in sales:
                all_sales.extend(sale.to_list_of_sales_info())
        else:
            failed_responses.append({
                'url': response.url,
                'status_code': response.status_code,
                'reason': response.reason
            })

    if failed_responses:
        failed_df = pd.DataFrame(failed_responses) \
            .groupby(['status_code', 'reason'], as_index=False).size() \
            .rename(columns={'size': 'count'}) \
            .sort_values('count', ascending=False)
        print('WARNING: Some requests failed:')
        print(tabulate(failed_df, headers='keys', showindex=False))

    sales_df = pd.DataFrame(all_sales)
    if sales_df.empty:
        raise Exception("Couldn't get any data from source, check the site's state in browser.")
    sales_df['Sell Date'] = pd.to_datetime(sales_df['Sell Date'])
    sales_df = sales_df.sort_values('Sell Date', ascending=False).reset_index(drop=True)
    return sales_df
