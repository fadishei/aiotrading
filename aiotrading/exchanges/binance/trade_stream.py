import logging
import asyncio
from datetime import datetime
from decimal import Decimal
from .market_stream import MarketStream
from ...types import Trade

log = logging.getLogger('aiotrading')

class TradeStream(MarketStream):

    def __init__(self, exchange, symbols):
        self.symbols = symbols
        names = [f'{symbol}@aggTrade' for symbol in symbols]
        super().__init__(exchange, names)

    async def write(self, msg):
        if msg['stream'] in self.names:
            d = msg['data']
            symbol = d['s'].lower()
            if f'{symbol}@aggTrade' in self.names: 
                t = Trade(
                    symbol = symbol,
                    id = d['a'],
                    time=datetime.fromtimestamp(d['T']/1000),
                    price=Decimal(d['p']),
                    volume=Decimal(d['q']),
                    buy = d['m']
                )
                await self.queue.put(t)

    def __str__(self):
        p = 's' if len(self.symbols)>1 else ''
        s = ', '.join(self.symbols)
        return f'trade stream{p} {s}'
