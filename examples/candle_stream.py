import asyncio
import logging
from aiotrading.exchanges.binance import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures() as exchange:
        async with exchange.candle_stream('btcusdt', '3m') as stream:
            for _ in range(10):
                data = await stream.read()
                log.info(data)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())