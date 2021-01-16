import logging
from decimal import Decimal
from datetime import datetime
from .market_stream import MarketStream
from ....types.trade import Trade

log = logging.getLogger('aiotrading')

class TradeStream(MarketStream):

    
    def __init__(self, exchange, symbol):
        super().__init__(exchange, f'{symbol}@aggTrade')
        self.symbol = symbol
        self.type = 'trade'

    async def write(self, d):
        t = Trade(
            id = d['a'],
            time=datetime.fromtimestamp(d['T']/1000),
            price=Decimal(d['p']),
            volume=Decimal(d['q']),
            buy = d['m'],
        )
        return await self.queue.put(t)
    
    def __str__(self):
        return f'{self.symbol}'
