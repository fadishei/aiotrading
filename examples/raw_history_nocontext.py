import asyncio
import logging
from aiotrading.exchanges.binance.futures import Exchange

log = logging.getLogger('aiotrading')

async def main():
    exchange = Exchange()
    await exchange.connect()
    params = {'symbol': 'BTCUSDT', 'interval': '1d', 'limit': 10}
    j = await exchange.get('klines', params=params)
    log.info(j)
    await exchange.disconnect()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())