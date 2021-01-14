import logging
import asyncio

log = logging.getLogger('aiotrading')

class CandleStream:

    def __init__(self, exchange, symbol, timeframe):
        self.exchange = exchange
        self.symbol = symbol
        self.timeframe = timeframe
        self.queue = asyncio.Queue()

    async def next_update(self):
        return await self.queue.get()

    async def close(self):
        await self.exchange.close_candle_stream(self)
