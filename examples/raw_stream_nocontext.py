import asyncio
import logging
from aiotrading.exchanges.binance import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    exchange = BinanceFutures()
    await exchange.connect()
    stream = exchange.market_stream('btcusdt@trade')
    await stream.open()
    for _ in range(10):
        data = await stream.read()
        log.info(data)
    await stream.close()
    await exchange.disconnect()
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())