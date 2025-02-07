import json
import requests

def get_api(category):
    param = { 'instType': category }
    param_str = '&'.join([f'{key}={param[key]}' for key in param.keys()])
    url = 'https://www.okx.com' + '/api/v5/market/tickers' + f'?{param_str}'
    response = requests.request('GET', url)
    return json.loads(response.text)

def get_tickers_temp(category):
    obj = get_api(category)
    arr = [ item['instId'] for item in obj['data'] ]
    arr = [ item.split('-')[0] for item in arr if item.split('-')[1] == 'USDT' ]
    return arr

def get_tickers():
    _spot = get_tickers_temp('SPOT')
    _line = get_tickers_temp('SWAP')
    ret = []
    for item in _spot:
        if item in _line:
            ret.append(item)
    return ret

if __name__ == '__main__':
    print( len(get_tickers()) )
