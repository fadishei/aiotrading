import asyncio
import logging
from aiotrading.exchange import BinanceFutures

async def main():
    exchange = BinanceFutures()
    await exchange.connect()
    candle_stream = await exchange.open_candle_stream('btcusdt', '3m')
    for i in range(10):
        candle = await candle_stream.next_update()
        log.info(candle)
    await candle_stream.close()
    await exchange.disconnect()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s: %(message)s')
    log = logging.getLogger('aiotrading')
    asyncio.get_event_loop().run_until_complete(main())