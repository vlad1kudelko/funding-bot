import asyncio
import json
import websockets

from get_tickers import get_tickers
symbols = [ x + '-USDT' for x in get_tickers() ]

async def main():
    url_okx = 'wss://ws.okx.com:8443/ws/v5/public'
    url_upd = 'ws://server:8000/update-ws'
    async with websockets.connect(url_okx) as ws_okx, websockets.connect(url_upd) as ws_upd:
        args = []
        for item_symbol in symbols:
            args.append({ 'channel': 'tickers',      'instId': item_symbol })
            args.append({ 'channel': 'tickers',      'instId': item_symbol + '-SWAP' })
            args.append({ 'channel': 'funding-rate', 'instId': item_symbol + '-SWAP' })
        subs = {
            'op': 'subscribe',
            'args': args,
        }
        await ws_okx.send(json.dumps(subs))
        async for msg in ws_okx:
            message = json.loads(msg)
            if message.setdefault('event', '') == 'subscribe':
                continue
            #--------------------------------------------------------
            if message['arg']['channel'] == 'tickers':
                if message['data'][0]['instType'] == 'SPOT':
                    place = 'spot'
                if message['data'][0]['instType'] == 'SWAP':
                    place = 'futures'
                symbol = message['data'][0]['instId'].split('-')[0]
                res = json.dumps({
                    symbol: {
                        'okx': {
                            place: {
                                'last': message['data'][0]['last'],
                                'ask': { 'price': message['data'][0]['askPx'], 'size': message['data'][0]['askSz'] },
                                'bid': { 'price': message['data'][0]['bidPx'], 'size': message['data'][0]['bidSz'] },
                            }
                        }
                    }
                })
                await ws_upd.send(res)
            #--------------------------------------------------------
            if message['arg']['channel'] == 'funding-rate':
                symbol = message['data'][0]['instId'].split('-')[0]
                res = json.dumps({
                    symbol: {
                        'okx': {
                            'futures': {
                                'funding': { 'rate': message['data'][0]['fundingRate'], 'time': message['data'][0]['fundingTime'] },
                            }
                        }
                    }
                })
                await ws_upd.send(res)
            #--------------------------------------------------------
            #  print(json.dumps(json.loads(msg), indent=4))

if __name__ == '__main__':
    asyncio.run(main())
