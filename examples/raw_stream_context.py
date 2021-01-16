import asyncio
import logging
from aiotrading.exchanges.binance.futures import Exchange

async def main():
    exchange = Exchange()
    async with exchange.market_stream('btcusdt@trade') as stream:
        for _ in range(10):
            data = await stream.read()
            log.info(data)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s: %(message)s')
    log = logging.getLogger('aiotrading')
    asyncio.get_event_loop().run_until_complete(main())