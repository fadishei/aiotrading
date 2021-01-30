import asyncio
import logging
from decimal import Decimal
from aiotrading import Order, OrderUpdateStream
from aiotrading.exchange import BinanceFutures

API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures(API_KEY, API_SECRET) as exchange:
        order = Order(symbol='btcusdt', size=Decimal('0.001'), type='limit',  side='buy',  price=Decimal('1000'), post_only=True)
        await exchange.submit_order(order)
        async with OrderUpdateStream(exchange, order) as stream:
            log.info('** please cancel the order in your binance account and see the update here')
            update = await stream.read()
            log.info(update)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')
    asyncio.get_event_loop().run_until_complete(main())