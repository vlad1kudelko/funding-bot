import json
import requests

def get_api(func, param):
    param_str = '&'.join([f'{key}={param[key]}' for key in param.keys()])
    url = f'https://api-testnet.bybit.com/v5/market/{func}?{param_str}'
    payload = {}
    headers = {}
    response = requests.request('GET', url, headers=headers, data=payload)
    return json.loads(response.text)
