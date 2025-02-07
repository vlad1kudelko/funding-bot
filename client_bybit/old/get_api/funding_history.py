from src.get_api import get_api

def get_api_funding_history(symbol):
    obj = get_api('funding/history', {
        'category': 'linear',
        'symbol': symbol,
    })
    arr = []
    for item in reversed(obj['result']['list']):
        arr.append({
            'fundingRateTimestamp': item['fundingRateTimestamp'],
            'fundingRate':          item['fundingRate'],
        })
    return arr
