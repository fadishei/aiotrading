# Introduction

Crypto exchange APIs are often callback-oriented. This makes coding a nightmare and will distract you from your most important goal of developing a winning strategy.

aiotrading is here to solve this problem. Using it, interacting with exchanges will be as much fun as the following [example](https://github.com/fadishei/aiotrading/blob/master/examples/candle_stream.py):

    from aiotrading import CandleStream
    from aiotrading.exchange import BinanceFutures

    async with BinanceFutures() as exchange:
        async with CandleStream(exchange, 'btcusdt', '3m') as stream:
            for i in range(10):
                candle = await stream.read()
                log.info(candle)
	    
Sample output of this code example is:

    connecting to exchange: binance-futures
    opening candle stream btcusdt@3m
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33800.00, l:33789.99, c:33795.18, v:4.164
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33800.00, l:33789.99, c:33799.76, v:4.481
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33800.00, l:33789.99, c:33797.73, v:4.741
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33800.00, l:33789.99, c:33797.47, v:5.132
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33800.89, l:33789.99, c:33797.39, v:5.520
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33800.89, l:33789.99, c:33797.38, v:5.605
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33800.89, l:33789.99, c:33797.39, v:6.000
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33807.99, l:33789.99, c:33806.80, v:16.562
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33807.99, l:33789.99, c:33797.70, v:16.590
    candle btcusdt, 3m, t:2021-01-30 11:39:00, o:33795.69, h:33807.99, l:33789.99, c:33794.60, v:17.342
    closing candle stream btcusdt@3m
    disconnecting from exchange: binance-futures

# Installation

    pip3 install aiotrading
    
# Design Principles

- **Thin portable API**. Lots of exchanges exist in the wild and developers like to migrate from exchange to exchange with no hassle.
- **Easy concurrency**. No callbacks as they distract from the goal and introduce errors.

# Status

aiotrading is at its early stage of development. It currently supports a subset of [Binance exchange API services](https://binance-docs.github.io/apidocs/futures/en/). More services will be supported in the future. It is designed in a way that other exchanges can be supported easily.