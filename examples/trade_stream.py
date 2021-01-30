import asyncio
import logging
from aiotrading import TradeStream
from aiotrading.exchange import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures() as exchange:
        async with TradeStream(exchange, 'btcusdt') as stream:
            for i in range(10):
                trade = await stream.read()
                log.info(trade)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())