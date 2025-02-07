from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket
import json
import pandas as pd
import polars as pl

app = FastAPI()
templates = Jinja2Templates(directory='templates')
#-------------------------------------------------------------------
SORT = 0
DATA = {}
DATA_example = {
    'example-BTC': {        # symbol
        'bybit': {          # market
            'spot': {       # place
                'last': '',
                'ask': { 'price': '', 'size': '' },  # ask, больше, продавцы, шортисты
                'bid': { 'price': '', 'size': '' },  # bid, меньше, покупатели, лонгисты
            },
            'futures': {
                'last': '',
                'ask': { 'price': '', 'size': '' },
                'bid': { 'price': '', 'size': '' },
                'funding': { 'rate': '', 'time': '' },
            },
        },
        'okx': {
            # ...
        },
    },
}
#-------------------------------------------------------------------
@app.websocket('/update-ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        global DATA
        obj = await websocket.receive_json()

        symbol = list(obj.keys())[0]
        if symbol not in DATA:
            DATA[symbol] = {}

        market = list(obj[symbol].keys())[0]
        if market not in DATA[symbol]:
            DATA[symbol][market] = {}

        place = list(obj[symbol][market].keys())[0]
        if place not in DATA[symbol][market]:
            DATA[symbol][market][place] = {}

        DATA[symbol][market][place] = {
            **DATA[symbol][market][place],
            **obj[symbol][market][place],
        }
#-------------------------------------------------------------------
def generate_html_table(data):
    html = '<table>'
    if data:
        html += '<thead><tr>'
        for i, header in enumerate(data[0].keys()):
            html += f'<th onclick="fetch(\'/sort/?by={i}\');" style="position:sticky;top:0px;" class="bg-slate-900">{header}</th>'
        html += '</tr></thead>'
        html += '<tbody>'

        sort_key = [key for j, key in enumerate(data[0].keys()) if j == (SORT if SORT > 0 else -SORT)][0]
        data = sorted(data, key=lambda x: x[sort_key])
        if SORT < 0:
            data = reversed(data)

        for i, item in enumerate(data):
            html += f'<tr>'
            for j, key in enumerate(item.keys()):
                cl = ''
                cl += 'text-red-500 '   if (isinstance(item[key], (int, float))) and (item[key] <  0) else ''
                cl += 'text-gray-700 '  if (isinstance(item[key], (int, float))) and (item[key] == 0) else ''
                cl += 'text-green-500 ' if (isinstance(item[key], (int, float))) and (item[key] >  0) else ''
                if isinstance(item[key], float):
                    spl = str(item[key]).split('.')
                    txt = spl[0].rjust(6, ' ') + '.' + spl[1].ljust(5, '0')[:5]
                else:
                    txt = item[key]
                html += f'<td id="td_{i}_{j}" class="{cl}">{txt}</td>'
            html += '</tr>'
        html += '</tbody>'
    html += '</table>'
    return html
#-------------------------------------------------------------------
@app.get('/sort/')
async def api_sort(by: int):
    global SORT
    if SORT == by:
        SORT = -by
    else:
        SORT = by
    return {}
#-------------------------------------------------------------------
@app.get('/get/')
async def api_get():
    fees = {
        'bybit': {
            'spot':    { 'maker': 0.1,   'taker': 0.18 },
            'futures': { 'maker': 0.036, 'taker': 0.1  },
        },
        'okx': {
            'spot':    { 'maker': 0.08, 'taker': 0.1  },
            'futures': { 'maker': 0.02, 'taker': 0.05 },
        },
    }
    ret = []
    for key in DATA.keys():
        ret.append({
            'symbol': key,

            'bybit spot ask price':         float(DATA[key].setdefault('bybit',{}).setdefault('spot',{}).setdefault('ask',{}).setdefault('price',0)),
            'bybit spot bid price':         float(DATA[key].setdefault('bybit',{}).setdefault('spot',{}).setdefault('bid',{}).setdefault('price',0)),
            'bybit futures ask price':      float(DATA[key].setdefault('bybit',{}).setdefault('futures',{}).setdefault('ask',{}).setdefault('price',0)),
            'bybit futures bid price':      float(DATA[key].setdefault('bybit',{}).setdefault('futures',{}).setdefault('bid',{}).setdefault('price',0)),
            'bybit futures funding rate':   float(DATA[key].setdefault('bybit',{}).setdefault('futures',{}).setdefault('funding',{}).setdefault('rate',0)) * 100,

            'okx spot ask price':           float(DATA[key].setdefault('okx',{}).setdefault('spot',{}).setdefault('ask',{}).setdefault('price',0)),
            'okx spot bid price':           float(DATA[key].setdefault('okx',{}).setdefault('spot',{}).setdefault('bid',{}).setdefault('price',0)),
            'okx futures ask price':        float(DATA[key].setdefault('okx',{}).setdefault('futures',{}).setdefault('ask',{}).setdefault('price',0)),
            'okx futures bid price':        float(DATA[key].setdefault('okx',{}).setdefault('futures',{}).setdefault('bid',{}).setdefault('price',0)),
            'okx futures funding rate':     float(DATA[key].setdefault('okx',{}).setdefault('futures',{}).setdefault('funding',{}).setdefault('rate',0)) * 100,
        })
    ret.sort(key=lambda x: x['symbol'])

    for key, _ in enumerate(ret):
        #  - на одной бирже между спотом и фьючами (2 шт)
        if (ret[key]['bybit spot ask price'] != 0) and (ret[key]['bybit futures bid price'] != 0):
            bybit_spot_L      = ret[key]['bybit spot ask price']    * (1 + fees['bybit']['spot']['maker']*2/100)
            bybit_futures_S   = ret[key]['bybit futures bid price'] * (1 - fees['bybit']['futures']['maker']*2/100)
            bybit_futures_pos = ret[key]['bybit futures bid price'] * (1 + fees['bybit']['futures']['maker']*2/100)
            funding           = ret[key]['bybit futures bid price'] * ret[key]['bybit futures funding rate']/100
            ret[key]['bybit spot L + futures S %'] = (bybit_futures_S + funding - bybit_spot_L) / (bybit_futures_pos + bybit_spot_L) * 100
        else:
            ret[key]['bybit spot L + futures S %'] = 0.0

        if (ret[key]['okx spot ask price'] != 0) and (ret[key]['okx futures bid price'] != 0):
            okx_spot_L      = ret[key]['okx spot ask price']    * (1 + fees['okx']['spot']['maker']*2/100)
            okx_futures_S   = ret[key]['okx futures bid price'] * (1 - fees['okx']['futures']['maker']*2/100)
            okx_futures_pos = ret[key]['okx futures bid price'] * (1 + fees['okx']['futures']['maker']*2/100)
            funding         = ret[key]['okx futures bid price'] * ret[key]['okx futures funding rate']/100
            ret[key]['okx spot L + futures S %'] = (okx_futures_S + funding - okx_spot_L) / (okx_futures_pos + okx_spot_L) * 100
        else:
            ret[key]['okx spot L + futures S %'] = 0.0

        ret[key]['bybit - okx funding %'] = (
            ret[key]['bybit futures funding rate'] -
            ret[key]['okx futures funding rate']
        )

        #  - между фьючами разных бирж (2 шт)
        if (ret[key]['bybit futures ask price'] != 0) and (ret[key]['okx futures bid price'] != 0):
            bybit_futures_L   = ret[key]['bybit futures ask price'] * (1 + fees['bybit']['futures']['maker']*2/100)
            okx_futures_S     = ret[key]['okx futures bid price']   * (1 - fees['okx']['futures']['maker']*2/100)
            okx_futures_pos   = ret[key]['okx futures bid price']   * (1 + fees['okx']['futures']['maker']*2/100)
            ret[key]['bybit futures L + okx futures S %'] = (okx_futures_S - bybit_futures_L) / (okx_futures_pos + bybit_futures_L) * 100 - ret[key]['bybit - okx funding %']
        else:
            ret[key]['bybit futures L + okx futures S %'] = 0.0

        if (ret[key]['okx futures ask price'] != 0) and (ret[key]['bybit futures bid price'] != 0):
            okx_futures_L     = ret[key]['okx futures ask price']   * (1 + fees['okx']['futures']['maker']*2/100)
            bybit_futures_S   = ret[key]['bybit futures bid price'] * (1 - fees['bybit']['futures']['maker']*2/100)
            bybit_futures_pos = ret[key]['bybit futures bid price'] * (1 + fees['bybit']['futures']['maker']*2/100)
            ret[key]['okx futures L + bybit futures S %'] = (bybit_futures_S - okx_futures_L) / (bybit_futures_pos + okx_futures_L) * 100 + ret[key]['bybit - okx funding %']
        else:
            ret[key]['okx futures L + bybit futures S %'] = 0.0

    return {'html': generate_html_table(ret)}
#-------------------------------------------------------------------
@app.get('/', response_class=HTMLResponse)
async def route_index(request: Request):
    return templates.TemplateResponse(request=request, name='list.html')
#-------------------------------------------------------------------
