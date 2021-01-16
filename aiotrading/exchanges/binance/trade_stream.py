import logging
from decimal import Decimal
from datetime import datetime
from .market_stream import MarketStream
from ...types.trade import Trade

log = logging.getLogger('aiotrading')

class TradeStream(MarketStream):

    
    def __init__(self, exchange, symbol):
        super().__init__(exchange, f'{symbol}@aggTrade')
        self.symbol = symbol
        self.type = 'trade'

    async def write(self, d):
        t = self.exchange.json_to_trade(d)
        return await self.queue.put(t)
    
    def __str__(self):
        return f'{self.symbol}'
