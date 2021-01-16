# Introduction

Crypto exchange APIs are often callback-oriented. This makes coding a nightmare and will distract you from your most important goal of developing a winning strategy.

aiotrading is here to solve this problem. Using it, interacting with exchanges will be as much fun as the following [example](https://github.com/fadishei/aiotrading/blob/master/examples/candle_stream.py):

    from aiotrading.exchanges.binance import BinanceFutures

    exchange = BinanceFutures()
    async with exchange.candle_stream('btcusdt', '3m') as stream:
        for _ in range(10):
            candle = await stream.read()
            log.info(candle)
	    
Sample output of this code example is:

    connecting to exchange: binance-futures
    opening canlde stream: btcusdt, 3m
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37230.00, c:37236.28, v:46.371
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37230.00, c:37233.00, v:47.567
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37230.00, c:37233.00, v:47.703
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37229.00, c:37229.01, v:57.839
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37229.00, c:37232.14, v:58.302
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37229.00, c:37229.00, v:58.527
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37229.00, c:37229.00, v:60.770
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37214.81, c:37214.81, v:75.948
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37210.00, c:37214.90, v:84.059
    t:2021-01-16 13:45:00, o:37305.99, h:37305.99, l:37210.00, c:37211.97, v:84.821
    closing canlde stream: btcusdt, 3m
    disconnecting from exchange: binance-futures

# Installation

    pip3 install aiotrading
    
# Status

aiotrading is at its early stage of development. It currently supports a subset of [Binance exchange API services](https://binance-docs.github.io/apidocs/futures/en/). More services will be supported in the future. It is designed in a way that other exchanges can be supported easily.