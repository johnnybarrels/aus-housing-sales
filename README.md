# aus-housing-sales

Scrape Australian property sales data.

## Usage

Install requirements

```shell
pip install -r requirements.txt
```

In `main.py`, edit state and list of suburbs, then run.

```python
if __name__ == '__main__':
    state = 'WA'
    suburbs = [
        'Scarborough',
        'Wembley Downs',
        'Doubleview'
    ]

    df = main(suburbs, state)
```

## Limitations

- Scrape resource only returns last 300 property sales (but also returns the previous sell price and sell date for these properties).
