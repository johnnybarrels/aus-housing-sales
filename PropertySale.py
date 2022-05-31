import re
import bs4
from copy import deepcopy


class PropertySale:
    data_selector = 'tr > td:nth-of-type(2) > table'
    sold_pat = re.compile(r'^Sold \$([0-9,]+) in ([a-zA-Z]{3} [0-9]{4})')
    last_sold_pat = re.compile(r'Last Sold \$([0-9,]+) in ([a-zA-Z]{3} [0-9]{4})')
    land_size_pat = re.compile(r'Land size: ([0-9]+) sqm')
    build_size_pat = re.compile(r'Building size: ([0-9]+) sqm')
    valid_property_types = [
        'House',
        'Unit',
        'Townhouse',
        'Apartment',
        'Villa',
        'Duplex',
        'Land'
    ]

    def __init__(self, item_html: bs4.element.Tag, suburb: str, state: str):
        self.item_html = item_html
        self.suburb = suburb
        self.state = state
        self.info = self.get_info_from_html()

    def get_info_from_html(self):
        item_data = self.item_html.select_one(self.data_selector)
        if item_data is None:
            raise ValueError('Item html is not in correct format to scrape.')

        data = {
            'Address': None,
            'Suburb': self.suburb,
            'State': self.state,
            'Type': None,
            'Sell Price': None,
            'Sell Date': None,
            'Last Sell Price': None,
            'Last Sell Date': None,
            'Bedrooms': None,
            'Bathrooms': None,
            'Car Ports': None,
            'Land Size': None,
            'Building Size': None
        }

        address, info = item_data.find_all('tr', recursive=False)

        data['Address'] = address.select_one('span.addr').get_text(strip=True)

        info_list = [x.text for x in info.select_one('table').select('td')]
        info_str = '\n'.join(info_list)

        if (sold_match := self.sold_pat.search(info_str)) is not None:
            sell_price, sell_date = sold_match.groups()
            data['Sell Price'] = self.int_from_str(sell_price)
            data['Sell Date'] = sell_date

        if (last_sold_match := self.last_sold_pat.search(info_str)) is not None:
            last_sell_price, last_sell_date = last_sold_match.groups()
            data['Last Sell Price'] = self.int_from_str(last_sell_price)
            data['Last Sell Date'] = last_sell_date

        props_data = [
            x for x in info_list if any(x.startswith(prop_type) for prop_type in self.valid_property_types)]
        if props_data:
            props_str = props_data[0]
            if 'land size' in props_str.lower():  # unknown property type, matched on 'Land Size' info
                pass
            else:
                property_type, num_stats = props_str.split(':', 1)
                data['Type'] = property_type.split()[0]

                for stat, num in zip(
                    ['Bedrooms', 'Bathrooms', 'Car Ports'],
                    num_stats.split()
                ):
                    data[stat] = int(num)

        if (land_size_match := self.land_size_pat.search(info_str)) is not None:
            data['Land Size'] = self.int_from_str(land_size_match.groups()[0])

        if (build_size_match := self.build_size_pat.search(info_str)) is not None:
            data['Building Size'] = self.int_from_str(build_size_match.groups()[0])

        return data

    @staticmethod
    def int_from_str(num_str):
        return int(num_str.replace(',', ''))

    def to_list_of_sales_info(self):
        info = deepcopy(self.info)
        last_sell_price, last_sell_date = info.pop('Last Sell Price'), info.pop('Last Sell Date')
        info['isPreviousSale'] = False
        res = [info]
        if last_sell_price is not None and last_sell_date is not None:
            last_sale_info = {k: v for k, v in info.items() if k not in ['Last Sell Price', 'Last Sell Date']}
            last_sale_info['Sell Price'] = last_sell_price
            last_sale_info['Sell Date'] = last_sell_date
            last_sale_info['isPreviousSale'] = True
            res.append(last_sale_info)
        return res

    def __repr__(self):
        return f'PropertySale({self.info.get("Address")!r}, suburb={self.suburb!r}, state={self.state!r})'
