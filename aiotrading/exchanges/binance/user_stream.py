import logging
import asyncio

log = logging.getLogger('aiotrading')

class UserStream:

    def __init__(self, exchange):
        self.exchange = exchange
        self.persistent = False
        self.queue = asyncio.Queue()

    async def read(self):
        return await self.queue.get()

    async def write(self, data):
        return await self.queue.put(data)

    async def open(self):
        await self.exchange.open_user_stream(self)

    async def close(self):
        await self.exchange.close_user_stream(self)

    def persist(self):
        self.persistent = True

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        
    def __str__(self):
        return 'user data stream'

    def __repr__(self):
        return self.__str__()
