import asyncio
import logging
from aiotrading.exchanges.binance import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures() as exchange:
        async with exchange.candles_stream([('btcusdt', '3m'), ('ethusdt', '1h')]) as stream:
            for i in range(10):
                candle = await stream.read()
                log.info(candle)
            log.info('*** there is an unnecessary stream reconnection here:')
        async with exchange.candles_stream([('btcusdt', '3m'), ('ethusdt', '1h')]) as stream:
            for i in range(10):
                candle = await stream.read()
                log.info(candle)
            log.info('*** you can avoid the extra stream reconnection by persisting the stream:')
            stream.persist()
        async with exchange.candles_stream([('btcusdt', '3m'), ('ethusdt', '1h')]) as stream:
            for i in range(10):
                candle = await stream.read()
                log.info(candle)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())