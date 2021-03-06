import asyncio
import logging
from decimal import Decimal
from aiotrading import CandleStream, Order, OrderUpdateStream, MixedStream
from aiotrading.exchange import BinanceFutures

API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'
SYMBOL = 'zecusdt'
SIZE = Decimal('0.02')
STOP = Decimal('0.5')

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures(API_KEY, API_SECRET) as exchange:
        log.info('waiting for current candle to close')
        async with CandleStream(exchange, SYMBOL, '1m') as stream:
            while True:
                candle = await stream.read()
                log.info(f'candle: {candle}')
                if candle.closed:
                    break
        log.info('creating orders')
        orders = [
            Order(symbol=SYMBOL, size=SIZE, type='market', side='sell', stop_price=candle.low-STOP, reduce_only=True),
            Order(symbol=SYMBOL, size=SIZE, type='market', side='buy', stop_price=candle.high+STOP, reduce_only=True),
            Order(symbol=SYMBOL, size=SIZE, type='limit',  side='buy',  price=candle.low),
            Order(symbol=SYMBOL, size=SIZE, type='limit',  side='sell', price=candle.high),
        ]
        for order in orders:
            await exchange.submit_order(order)
        log.info('watching updates from orders')
        async with MixedStream([OrderUpdateStream(exchange, o) for o in orders]) as stream:
            while True:
                update = await stream.read()
                log.info(update)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')
    asyncio.get_event_loop().run_until_complete(main())