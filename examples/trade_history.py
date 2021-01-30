import asyncio
import logging
from datetime import datetime
from aiotrading.exchange import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures() as exchange:
        trades = await exchange.trade_history('btcusdt', datetime(2020, 1, 1), 10)
        pretty = '\n'.join([str(t) for t in trades])
        log.info(pretty)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())