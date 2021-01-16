import logging
import asyncio
import json
import aiohttp
import websockets
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
from websockets.exceptions import ConnectionClosedOK
from .market_stream import MarketStream
from .candle_stream import CandleStream
from .trade_stream import TradeStream
from ....types import Candle

log = logging.getLogger('aiotrading')

class Exchange:

    def __init__(self):
        self.name = 'binance-futures'
        self.market_streams = defaultdict(set)
        self.market_streams_count = 0
        self.market_streams_lock = asyncio.Lock()
        self.market_websocket_uri = 'wss://fstream.binance.com/'
        self.restful_uri = 'https://fapi.binance.com/fapi/v1/'

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def connect(self):
        log.info(f'connecting to exchange: {self.name}')
        self.restful_session = aiohttp.ClientSession()
        
    async def disconnect(self):
        log.info(f'disconnecting from exchange: {self.name}')
        await self.restful_session.close()
        
    def market_stream(self, name):
        return MarketStream(self, name)

    def candle_stream(self, symbol, timeframe):
        return CandleStream(self, symbol, timeframe)

    def trade_stream(self, symbol):
        return TradeStream(self, symbol)

    async def candle_history(self, symbol, timeframe, start_time, count, batch=1500):
        log.info(f'fetching candle history of length {count} for {symbol}, {timeframe} from {start_time}')
        candles = []
        remained = count
        while remained>0:
            count = min(remained, batch)
            log.debug(f'batch: {start_time}, {count}')
            params = {'symbol': symbol.upper(), 'interval': timeframe, 'startTime': int(start_time.timestamp()*1000), 'limit': count}
            j = await self.get('klines', params=params)
            if len(j) == 0:
                break
            for d in j:
                c = Candle(open_time=datetime.fromtimestamp(d[0]/1000),
                    open=Decimal(d[1]), high=Decimal(d[2]), low=Decimal(d[3]), close=Decimal(d[4]),
                    volume=Decimal(d[5]), trades=d[8], buy_volume=Decimal(d[9]),
                    closed=True, update_time=datetime.fromtimestamp(d[6]/1000))
                candles.append(c)
            remained -= count
            start_time = candles[-1].open_time+timedelta(minutes=1)
        return candles
        
    async def get(self, endpoint, params, sign=False):
        async with self.restful_session.get(self.restful_uri+endpoint, params=params) as resp:
            log.debug(f'restful request status: {resp.status}')
            return await resp.json()
        
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
                uri = f'{self.market_websocket_uri}stream?streams={name}'
                log.debug(f'connecting to market websocket stream of {self.name} at {uri}')
                self.market_websocket = await websockets.connect(uri)
                asyncio.get_event_loop().create_task(self.market_websocket_task())
            elif len(self.market_streams[name]) == 1:
                log.debug(f'subscribing to market websocket stream of {self.name} to {name}')
                msg = json.dumps({'method': 'SUBSCRIBE', 'params': [name], 'id': 1})
                await self.market_websocket.send(msg)

    async def close_market_stream(self, stream):
        async with self.market_streams_lock:
            name = stream.name
            if name not in self.market_streams or stream not in self.market_streams[name]:
                log.error(f'stream {name} is not open')
                return
            if self.market_streams_count == 1:
                log.debug(f'disconnecting from market websocket stream of {self.name}')
                await self.market_websocket.close()
            elif len(self.market_streams[name]) == 1:
                log.debug(f'unsubscribing from market websocket stream of {self.name} from {name}')
                msg = json.dumps({'method': 'UNSUBSCRIBE', 'params': [name], 'id': 1})
                await self.market_websocket.send(msg)        
            stream_set = self.market_streams[name]
            stream_set.remove(stream)
            self.market_streams_count -= 1
                