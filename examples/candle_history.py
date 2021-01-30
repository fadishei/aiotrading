import asyncio
import logging
from datetime import datetime
from aiotrading.exchange import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures() as exchange:
        candles = await exchange.candle_history('btcusdt', '1d', datetime(2021, 1, 1), 10)
        pretty = '\n'.join([str(c) for c in candles])
        log.info(pretty)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())