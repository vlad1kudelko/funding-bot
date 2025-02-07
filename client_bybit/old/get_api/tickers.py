from src.get_api import get_api

def get_api_tickers():
    obj = get_api('tickers', {
        'category': 'linear',
    })
    arr = []
    for item in reversed(obj['result']['list']):
        if item['fundingRate'] != '':
            arr.append({
                'symbol':           item['symbol'],
                'lastPrice':        item['lastPrice'],
                'fundingRate':      item['fundingRate'],
                'nextFundingTime':  item['nextFundingTime'],
            })
    return arr
