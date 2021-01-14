# Introduction

Crypto exchange APIs are often callback-oriented. This makes coding a nightmare and will distract you from your most important goal of developing a winning strategy.

aiotrading is here to solve this problem. Using it, interacting with exchanges will be as much fun as the following example:

    import asyncio
    import logging
    from aiotrading.exchange import BinanceFutures

    async def main():
        exchange = BinanceFutures()
        await exchange.connect()
        candle_stream = await exchange.open_candle_stream('btcusdt', '3m')
        for i in range(10):
            candle = await candle_stream.next_update()
            log.info(candle)
        await candle_stream.close()
        await exchange.disconnect()

    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s: %(message)s')
        log = logging.getLogger('aiotrading')
        asyncio.get_event_loop().run_until_complete(main())
	    
Sample output of this code example is:

    2021-01-14 17:50:58,785-INFO: connecting to exchange
    2021-01-14 17:51:00,838-INFO: opening candle stream btcusdt@3m
    2021-01-14 17:51:00,838-INFO: subscribing to websocket for btcusdt@3m
    2021-01-14 17:51:01,311-INFO: o:39534.56, h:39570.00, l:39522.00, c:39563.49, v:299.306
    2021-01-14 17:51:01,480-INFO: o:39534.56, h:39570.00, l:39522.00, c:39563.65, v:299.506
    2021-01-14 17:51:01,959-INFO: o:39563.75, h:39564.61, l:39563.75, c:39564.61, v:0.086
    2021-01-14 17:51:02,341-INFO: o:39563.75, h:39564.61, l:39563.75, c:39564.53, v:0.119
    2021-01-14 17:51:02,830-INFO: o:39563.75, h:39564.61, l:39563.75, c:39564.52, v:0.424
    2021-01-14 17:51:03,195-INFO: o:39563.75, h:39564.61, l:39558.87, c:39561.29, v:6.059
    2021-01-14 17:51:03,640-INFO: o:39563.75, h:39564.61, l:39558.87, c:39564.53, v:7.072
    2021-01-14 17:51:04,067-INFO: o:39563.75, h:39564.61, l:39556.84, c:39561.78, v:8.487
    2021-01-14 17:51:04,331-INFO: o:39563.75, h:39564.61, l:39556.84, c:39560.68, v:8.539
    2021-01-14 17:51:04,803-INFO: o:39563.75, h:39564.61, l:39556.84, c:39560.70, v:8.592
    2021-01-14 17:51:04,804-INFO: closing candle stream btcusdt@3m
    2021-01-14 17:51:04,805-INFO: unsubscribing from websocket for btcusdt@3m
    2021-01-14 17:51:04,806-INFO: disconnecting from exchange

# Installation

    pip3 install aiotrading
    
# Status

aiotrading is at its early stage of development. It currently supports a subset of [Binance exchange API services](https://binance-docs.github.io/apidocs/futures/en/). More services will be supported in the future. It is designed in a way that other exchanges can be supported easily.