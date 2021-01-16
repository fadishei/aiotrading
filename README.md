# Introduction

Crypto exchange APIs are often callback-oriented. This makes coding a nightmare and will distract you from your most important goal of developing a winning strategy.

aiotrading is here to solve this problem. Using it, interacting with exchanges will be as much fun as the following [example](examples/candle_stream.py):

    from aiotrading.exchanges.binance.futures import Exchange

    exchange = Exchange()
    async with exchange.candle_stream('btcusdt', '3m') as stream:
        for _ in range(10):
            candle = await stream.read()
            log.info(candle)
	    
Sample output of this code example is:

    2021-01-16 00:19:48,696-INFO: creating exchange: binance-futures                       
    2021-01-16 00:19:48,697-INFO: opening canlde stream: btcusdt, 3m
    2021-01-16 00:19:50,718-INFO: o:37343.16, h:37345.91, l:37250.00, c:37256.14, v:270.707
    2021-01-16 00:19:51,129-INFO: o:37343.16, h:37345.91, l:37250.00, c:37259.07, v:270.712
    2021-01-16 00:19:51,515-INFO: o:37343.16, h:37345.91, l:37250.00, c:37259.08, v:270.789
    2021-01-16 00:19:51,806-INFO: o:37343.16, h:37345.91, l:37250.00, c:37255.81, v:271.064
    2021-01-16 00:19:52,209-INFO: o:37343.16, h:37345.91, l:37250.00, c:37255.23, v:271.158
    2021-01-16 00:19:52,452-INFO: o:37343.16, h:37345.91, l:37250.00, c:37255.61, v:271.191
    2021-01-16 00:19:52,705-INFO: o:37343.16, h:37345.91, l:37250.00, c:37250.00, v:284.017
    2021-01-16 00:19:53,074-INFO: o:37343.16, h:37345.91, l:37249.74, c:37249.74, v:284.722
    2021-01-16 00:19:53,378-INFO: o:37343.16, h:37345.91, l:37249.74, c:37250.03, v:284.819
    2021-01-16 00:19:53,960-INFO: o:37343.16, h:37345.91, l:37249.74, c:37250.03, v:285.049
    2021-01-16 00:19:53,962-INFO: closing canlde stream: btcusdt, 3m

# Installation

    pip3 install aiotrading
    
# Status

aiotrading is at its early stage of development. It currently supports a subset of [Binance exchange API services](https://binance-docs.github.io/apidocs/futures/en/). More services will be supported in the future. It is designed in a way that other exchanges can be supported easily.