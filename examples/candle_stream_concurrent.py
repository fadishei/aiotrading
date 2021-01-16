import asyncio
import logging
from aiotrading.exchanges.binance import BinanceFutures

log = logging.getLogger('aiotrading')
finished = False

async def consume(stream):
    while not finished:
        candle = await stream.read()
        log.info(f'{stream.symbol}, {stream.timeframe}: {candle}')

async def main():
    async with BinanceFutures() as exchange:
        stream1 = exchange.candle_stream('btcusdt', '3m')
        stream2 = exchange.candle_stream('ethusdt', '1h')
        await asyncio.wait([stream1.open(), stream2.open()])
        await asyncio.wait([consume(stream1), consume(stream2)])
        await asyncio.wait([stream1.close(), stream2.close()])
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        finished = True
        cleanup = asyncio.gather(*asyncio.all_tasks(loop=loop), loop=loop, return_exceptions=True)
        loop.run_until_complete(cleanup)