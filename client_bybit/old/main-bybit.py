from tabulate import tabulate
import datetime

from src.get_api.tickers import get_api_tickers
from src.get_api.funding_history import get_api_funding_history
from src.get_color import get_color

#  dt = datetime.datetime.utcfromtimestamp(
    #  int(item['fundingRateTimestamp'])/1000).isoformat()


tickers = get_api_tickers()
for key, ticker in enumerate(tickers):
    if float(ticker['fundingRate']) > 0.01:
        tickers[key]['fundingRate'] = get_color(ticker['fundingRate'], 'blue')
tickers_tbl = tabulate(tickers, tablefmt='github', headers='keys').split('\n')

if True:
    print('\n'.join(tickers_tbl))
else:
    print(tickers_tbl[0])
    print(tickers_tbl[1])
    for key, ticker in enumerate(tickers):
        arr_funding = reversed(list(map(
            lambda a: a['fundingRate'],
            get_api_funding_history(ticker['symbol'])[-5:],
        )))
        color_funding = []
        for item_fund in arr_funding:
            if float(item_fund) > 0.01:
                color_funding.append(get_color(item_fund, 'blue'))
            else:
                color_funding.append(item_fund)
        print(' > '.join([
            tickers_tbl[key+2],
            ' / '.join(color_funding)
        ]))
