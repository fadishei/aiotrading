import logging
import asyncio

log = logging.getLogger('aiotrading')

class MarketStream:

    def __init__(self, exchange, name):
        self.exchange = exchange
        self.name = name
        self.type = 'market'
        self.queue = asyncio.Queue()

    async def read(self):
        return await self.queue.get()

    async def write(self, data):
        return await self.queue.put(data)

    async def open(self):
        log.info(f'opening {self.type} stream: {self}')
        await self.exchange.open_market_stream(self)

    async def close(self):
        log.info(f'closing {self.type} stream: {self}')
        await self.exchange.close_market_stream(self)
        
    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()
