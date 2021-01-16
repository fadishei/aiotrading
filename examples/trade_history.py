import asyncio
import logging
from datetime import datetime
from aiotrading.exchanges.binance.futures import Exchange

log = logging.getLogger('aiotrading')

async def main():
    async with Exchange() as exchange:
        trades = await exchange.trade_history('btcusdt', datetime(2020, 1, 1), 10)
        pretty = '\n'.join([str(t) for t in trades])
        log.info(f'result:\n{pretty}')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())