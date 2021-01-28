import asyncio
import logging
from aiotrading.exchanges.binance import BinanceFutures

API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures(API_KEY, API_SECRET) as exchange:
        async with exchange.user_stream() as stream:
            data = await stream.read()
            log.info(data)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())