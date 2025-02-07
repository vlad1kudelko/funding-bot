from pybit.unified_trading import WebSocket
from time import sleep
from websockets.sync.client import connect
import json

from get_tickers import get_tickers
glob_symbol = [ x + 'USDT' for x in get_tickers() ]

def main():
    url_upd = 'ws://server:8000/update-ws'
    with connect(url_upd) as ws_upd:
        #------------------------------------------------------------
        ws_linear = WebSocket(
            testnet=False,
            channel_type='linear',
        )
        def handle_message_linear(message):
            symbol = message['data']['symbol']
            if symbol.endswith('USDT'):
                symbol = symbol[:-4]
            res = json.dumps({
                symbol: {
                    'bybit': {
                        'futures': {
                            'last': message['data']['lastPrice'],
                            'ask': { 'price': message['data']['ask1Price'], 'size': message['data']['ask1Size'] },
                            'bid': { 'price': message['data']['bid1Price'], 'size': message['data']['bid1Size'] },
                            'funding': { 'rate': message['data']['fundingRate'], 'time': message['data']['nextFundingTime'] },
                        }
                    }
                }
            })
            ws_upd.send(res)

        for item_symbol in glob_symbol:
            #  фандинг и текущая цена
            ws_linear.ticker_stream(
                symbol=item_symbol,
                callback=handle_message_linear
            )
        #------------------------------------------------------------
        ws_spot = WebSocket(
            testnet=False,
            channel_type='spot',
        )
        def handle_message_spot(message):
            symbol = message['data']['s']
            if symbol.endswith('USDT'):
                symbol = symbol[:-4]
            res = json.dumps({
                symbol: {
                    'bybit': {
                        'spot': {
                            'last': '',
                            'ask': { 'price': message['data']['a'][0][0], 'size': message['data']['a'][0][1] },
                            'bid': { 'price': message['data']['b'][0][0], 'size': message['data']['b'][0][1] },
                        }
                    }
                }
            })
            ws_upd.send(res)

        for item_symbol in glob_symbol:
            #  стакан с объемами
            ws_spot.orderbook_stream(
                depth=1,
                symbol=item_symbol,
                callback=handle_message_spot
            )
        #------------------------------------------------------------
        while True:
            sleep(5)

if __name__ == '__main__':
    main()
