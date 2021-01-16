import logging
from decimal import Decimal
from datetime import datetime
from .market_stream import MarketStream

log = logging.getLogger('aiotrading')

class CandleStream(MarketStream):

    def __init__(self, exchange, symbol, timeframe):
        super().__init__(exchange, f'{symbol}@kline_{timeframe}')
        self.symbol = symbol
        self.timeframe = timeframe
        self.type = 'canlde'

    async def write(self, d):
        c = self.exchange.json_to_candle_websocket(d)
        return await self.queue.put(c)
    
    def __str__(self):
        return f'{self.symbol}, {self.timeframe}'
