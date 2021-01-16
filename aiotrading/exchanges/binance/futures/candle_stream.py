import logging
from decimal import Decimal
from datetime import datetime
from .market_stream import MarketStream
from ....types.candle import Candle

log = logging.getLogger('aiotrading')

class CandleStream(MarketStream):

    def __init__(self, exchange, symbol, timeframe):
        super().__init__(exchange, f'{symbol}@kline_{timeframe}')
        self.symbol = symbol
        self.timeframe = timeframe
        self.type = 'canlde'

    async def write(self, d):
        c = Candle(
            open_time=datetime.fromtimestamp(d['k']['t']/1000),
            update_time=datetime.fromtimestamp(d['E']/1000),
            open=Decimal(d['k']['o']),
            high=Decimal(d['k']['h']),
            low=Decimal(d['k']['l']),
            close=Decimal(d['k']['c']),
            volume=Decimal(d['k']['v']),
            buy_volume = Decimal(d['k']['V']),
            trades=int(d['k']['n']),
            closed=d['k']['x'],
        )
        return await self.queue.put(c)
    
    def __str__(self):
        return f'{self.symbol}, {self.timeframe}'
