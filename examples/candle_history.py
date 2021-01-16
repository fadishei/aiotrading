import asyncio
import logging
from datetime import datetime
from aiotrading.exchanges.binance.futures import Exchange

async def main():
    async with Exchange() as exchange:
        candles = await exchange.candle_history('btcusdt', '1d', datetime(2021, 1, 1), 10)
        pretty = '\n'.join([str(c) for c in candles])
        log.info(f'result:\n{pretty}')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s: %(message)s')
    log = logging.getLogger('aiotrading')
    asyncio.get_event_loop().run_until_complete(main())