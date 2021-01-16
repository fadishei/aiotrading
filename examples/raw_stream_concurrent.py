import asyncio
import logging
from aiotrading.exchanges.binance.futures import Exchange

finished = False

async def report(stream):
    while not finished:
        data = await stream.read()
        log.info(data)

async def main():
    async with Exchange() as exchange:
        stream1 = exchange.market_stream('btcusdt@kline_3m')
        stream2 = exchange.market_stream('ethusdt@trade')
        await asyncio.wait([stream1.open(), stream2.open()])
        await asyncio.wait([report(stream1), report(stream2)])
        await asyncio.wait([stream1.close(), stream2.close()])
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s: %(message)s')
    log = logging.getLogger('aiotrading')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        finished = True
        cleanup = asyncio.gather(*asyncio.all_tasks(loop=loop), loop=loop, return_exceptions=True)
        loop.run_until_complete(cleanup)