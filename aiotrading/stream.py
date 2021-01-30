import asyncio
import logging

log = logging.getLogger('aiotrading')

class Stream:

    def __init__(self, exchange):
        self.exchange = exchange
        self.queue = asyncio.Queue()

    async def read(self):
        return await self.queue.get()

    async def write(self, d):
        await self.queue.put(d)

    async def open(self):
        await self.exchange.open_stream(self)

    async def close(self):
        await self.exchange.close_stream(self)
        
    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
    
    def __str__(self):
        return f'generic stream'

    def __repr__(self):
        return self.__str__()

class CandleStream(Stream):

    def __init__(self, exchange, symbol, timeframe):
        super().__init__(exchange)
        self.symbol = symbol
        self.timeframe = timeframe

    def __str__(self):
        return f'candle stream {self.symbol}@{self.timeframe}'

class TradeStream(Stream):

    def __init__(self, exchange, symbol):
        super().__init__(exchange)
        self.symbol = symbol

    def __str__(self):
        return f'trade stream {self.symbol}'

class OrderUpdateStream(Stream):

    def __init__(self, exchange, order=None):
        super().__init__(exchange)
        self.order = order

    def __str__(self):
        return f'order update stream {self.order.id}'

class MixedStream:

    def __init__(self, streams):
        self.streams = streams
        self.queue = asyncio.Queue()

    async def read(self):
        return await self.queue.get()

    async def worker(self, stream):
        while True:
            d = await stream.read()
            await self.queue.put((stream, d))
        
    async def open(self):
        log.info(f'opening {self}')
        self.tasks = [asyncio.get_event_loop().create_task(self.worker(stream)) for stream in self.streams]
        for stream in self.streams:
            await stream.open()

    async def close(self):
        log.info(f'closing {self}')
        await asyncio.wait([stream.close() for stream in self.streams], return_when=asyncio.ALL_COMPLETED)
        for task in self.tasks:
            task.cancel()
        await asyncio.wait(self.tasks, return_when=asyncio.ALL_COMPLETED)

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
    
    def __str__(self):
        s = ', '.join([str(s) for s in self.streams])
        return f'mixed stream {s}'

    def __repr__(self):
        return self.__str__()
