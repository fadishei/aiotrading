import asyncio
import logging
from aiotrading import CandleStream
from aiotrading.exchange import BinanceFutures

log = logging.getLogger('aiotrading')
finish = False

async def watch_market(exchange, symbol):
    async with CandleStream(exchange, symbol, '1h') as stream:
        while not finish:
            candle = await stream.read()
            log.info(candle)
        
async def main():
    async with BinanceFutures() as exchange:
        symbols = ['btcusdt', 'ethusdt']
        watch_market_tasks = [asyncio.get_event_loop().create_task(watch_market(exchange, symbol)) for symbol in symbols]
        await asyncio.wait(watch_market_tasks)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        finish = True
        cleanup = asyncio.gather(*asyncio.all_tasks(loop=loop), loop=loop, return_exceptions=True)
        loop.run_until_complete(cleanup)