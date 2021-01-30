import asyncio
import logging
from aiotrading import CandleStream
from aiotrading.exchange import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures() as exchange:
        async with CandleStream(exchange, 'btcusdt', '3m') as stream:
            for i in range(10):
                candle = await stream.read()
                log.info(candle)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())