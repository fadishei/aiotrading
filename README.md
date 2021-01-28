# Introduction

Crypto exchange APIs are often callback-oriented. This makes coding a nightmare and will distract you from your most important goal of developing a winning strategy.

aiotrading is here to solve this problem. Using it, interacting with exchanges will be as much fun as the following [example](https://github.com/fadishei/aiotrading/blob/master/examples/candle_stream.py):

    from aiotrading.exchanges.binance import BinanceFutures

    async with BinanceFutures() as exchange:
        async with exchange.candle_stream('btcusdt', '3m') as stream:
            for i in range(10):
                candle = await stream.read()
                log.info(candle)
	    
Sample output of this code example is:

    connecting to exchange: binance-futures
    opening candle stream btcusdt@3m
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32388.45, v:410.773
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32383.49, v:410.948
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32380.14, v:411.627
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32380.43, v:414.070
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32382.41, v:414.448
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32377.47, v:415.138
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32376.50, v:416.437
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32374.96, v:417.523
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32373.64, v:417.749
    btcusdt, 3m, t:2021-01-28 16:54:00, o:32340.44, h:32437.67, l:32324.00, c:32382.07, v:422.761
    closing candle stream btcusdt@3m
    disconnecting from exchange: binance-futures

# Installation

    pip3 install aiotrading
    
# Status

aiotrading is at its early stage of development. It currently supports a subset of [Binance exchange API services](https://binance-docs.github.io/apidocs/futures/en/). More services will be supported in the future. It is designed in a way that other exchanges can be supported easily.