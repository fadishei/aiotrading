import logging
import asyncio
import json
import websockets
from collections import defaultdict
from websockets.exceptions import ConnectionClosedOK
from .market_stream import MarketStream
from .candle_stream import CandleStream
from .trade_stream import TradeStream

log = logging.getLogger('aiotrading')

class Exchange:

    name = 'binance-futures'
    market_websocket_uri = 'wss://fstream.binance.com/'

    def __init__(self):
        log.info(f'creating exchange: {Exchange.name}')
        self.market_streams = defaultdict(set)
        self.market_streams_count = 0
        self.market_streams_lock = asyncio.Lock()

    def market_stream(self, name):
        return MarketStream(self, name)

    def candle_stream(self, symbol, timeframe):
        return CandleStream(self, symbol, timeframe)

    def trade_stream(self, symbol):
        return TradeStream(self, symbol)

    async def market_websocket_task(self):
        log.debug('starting market websocket task')
        while True:
            try:
                msg = await self.market_websocket.recv()
            except ConnectionClosedOK:
                break
            j = json.loads(msg)
            if 'stream' in j and 'data' in j:
                d = j['data']
                s = j['stream']
                if s in self.market_streams:
                    for stream in self.market_streams[s]:
                        await stream.write(d)
        log.debug('market websocket task stopped')
    
    async def open_market_stream(self, stream):
        async with self.market_streams_lock:
            name = stream.name
            self.market_streams[name].add(stream)
            self.market_streams_count += 1
            if self.market_streams_count == 1:
                uri = f'{Exchange.market_websocket_uri}stream?streams={name}'
                log.debug(f'connecting to market websocket stream of {Exchange.name} at {uri}')
                self.market_websocket = await websockets.connect(uri)
                asyncio.get_event_loop().create_task(self.market_websocket_task())
            elif len(self.market_streams[name]) == 1:
                log.debug(f'subscribing to market websocket stream of {Exchange.name} to {name}')
                msg = json.dumps({'method': 'SUBSCRIBE', 'params': [name], 'id': 1})
                await self.market_websocket.send(msg)

    async def close_market_stream(self, stream):
        async with self.market_streams_lock:
            name = stream.name
            if name not in self.market_streams or stream not in self.market_streams[name]:
                log.error(f'stream {name} is not open')
                return
            if self.market_streams_count == 1:
                log.debug(f'disconnecting from market websocket stream of {Exchange.name}')
                await self.market_websocket.close()
            elif len(self.market_streams[name]) == 1:
                log.debug(f'unsubscribing from market websocket stream of {Exchange.name} from {name}')
                msg = json.dumps({'method': 'UNSUBSCRIBE', 'params': [name], 'id': 1})
                await self.market_websocket.send(msg)        
            stream_set = self.market_streams[name]
            stream_set.remove(stream)
            self.market_streams_count -= 1
                