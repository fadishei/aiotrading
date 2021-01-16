import asyncio
import logging
from aiotrading.exchanges.binance.futures import Exchange

log = logging.getLogger('aiotrading')

async def main():
    async with Exchange() as exchange:
        async with exchange.trade_stream('btcusdt') as stream:
            for _ in range(10):
                data = await stream.read()
                log.info(data)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())