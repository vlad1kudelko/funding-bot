import json
import requests

def get_api(func, param):
    param_str = '&'.join([f'{key}={param[key]}' for key in param.keys()])
    url = f'https://api-testnet.bybit.com/v5/market/{func}?{param_str}'
    payload = {}
    headers = {}
    response = requests.request('GET', url, headers=headers, data=payload)
    return json.loads(response.text)

def get_tickers_temp(category):
    obj = get_api('tickers', {'category': category})
    arr = [ item['symbol'] for item in obj['result']['list'] ]
    return arr

def get_tickers():
    _spot = get_tickers_temp('spot')
    _line = get_tickers_temp('linear')
    ret = []
    for item in _spot:
        if item in _line:
            if item.endswith('USDT'):
                ret.append(item[:-4])
    return ret

if __name__ == '__main__':
    print( len(get_tickers()) )
