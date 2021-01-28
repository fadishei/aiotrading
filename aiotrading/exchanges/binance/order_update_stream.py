import logging
import asyncio
from datetime import datetime
from decimal import Decimal
from .user_stream import UserStream
from ...types import OrderUpdate

log = logging.getLogger('aiotrading')

class OrderUpdateStream(UserStream):

    def __init__(self, exchange, orders=None):
        self.orders = None if orders is None else {o.id: o for o in orders}
        super().__init__(exchange)

    async def write(self, msg):
        if 'e' in msg and msg['e'] == 'ORDER_TRADE_UPDATE':
            d = msg['o']
            if self.orders is None or d['c'] in self.orders:
                ou = OrderUpdate(
                    order=self.orders[d['c']],
                    time=datetime.fromtimestamp(msg['T']/1000),
                    status=self.status(d['X']),
                    size=Decimal(d['l']),
                    total_size=Decimal(d['z']),
                    price=Decimal(d['L']),
                    average_price=Decimal(d['ap']),
                )
                await self.queue.put(ou)

    def status(self, s):
        if s == 'NEW':
            return 'submit'
        elif s == 'PARTIALLY_FILLED':
            return 'partial'
        elif s == 'FILLED':
            return 'fill'
        elif s == 'CANCELED':
            return 'cancel'
        elif s == 'EXPIRED':
            return 'expire'
        else:
            return s
      
    def __str__(self):
        p = 's' if len(self.orders)>1 else ''
        s = ', '.join(self.orders)
        return f'order update stream{p} {s}'
