import logging
import asyncio
from datetime import datetime
from decimal import Decimal
from .market_stream import MarketStream
from ...types import Candle

log = logging.getLogger('aiotrading')

class CandleStream(MarketStream):

    def __init__(self, exchange, candle_specs):
        self.candle_specs = candle_specs
        names = [f'{symbol}@kline_{timeframe}' for symbol, timeframe in candle_specs]
        super().__init__(exchange, names)

    async def write(self, msg):
        if msg['stream'] in self.names:
            d = msg['data']
            symbol = d['s'].lower()
            timeframe = d['k']['i']
            if f'{symbol}@kline_{timeframe}' in self.names: 
                c = Candle(
                    symbol = symbol,
                    timeframe = timeframe,
                    open_time=datetime.fromtimestamp(d['k']['t']/1000),
                    update_time=datetime.fromtimestamp(d['k']['T']/1000), #?d['E']
                    open=Decimal(d['k']['o']),
                    high=Decimal(d['k']['h']),
                    low=Decimal(d['k']['l']),
                    close=Decimal(d['k']['c']),
                    volume=Decimal(d['k']['v']),
                    buy_volume = Decimal(d['k']['V']),
                    trades=int(d['k']['n']),
                    closed=d['k']['x']
                )
                await self.queue.put(c)

    def __str__(self):
        ss = [f'{symbol}@{timeframe}' for symbol, timeframe in self.candle_specs]
        p = 's' if len(ss)>1 else ''
        s = ', '.join(ss)
        return f'candle stream{p} {s}'
