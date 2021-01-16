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
from ....types.trade import Trade
from ....types.candle import Candle

log = logging.getLogger('aiotrading')

class Exchange:

    def __init__(self):
        self.name = 'binance-futures'
        self.market_streams = defaultdict(set)
        self.market_streams_count = 0
        self.market_streams_lock = asyncio.Lock()
        self.market_websocket_uri = 'wss://fstream.binance.com/'
        self.restful_uri = 'https://fapi.binance.com/fapi/v1/'

    async def connect(self):
        log.info(f'connecting to exchange: {self}')
        self.restful_session = aiohttp.ClientSession()
        
    async def disconnect(self):
        log.info(f'disconnecting from exchange: {self}')
        await self.restful_session.close()
        
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
                c = self.json_to_candle_restful(d)
                candles.append(c)
            remained -= count
            start_time = candles[-1].open_time+timedelta(minutes=1)
        return candles
        
    async def trade_history_from_id(self, symbol, start_id, count, batch=1000):
        log.info(f'fetching trade history of length {count} for {symbol} from id {start_id}')
        trades = []
        remained = count
        while remained>0:
            count = min(remained, batch)
            log.debug(f'batch: {start_id}, {count}')
            params = {'symbol': symbol.upper(), 'fromId': start_id, 'limit': count}
            j = await self.get('aggTrades', params=params)
            if len(j) == 0:
                break
            for d in j:
                t = self.json_to_trade(d)
                trades.append(t)
            remained -= count
            start_id = trades[-1].id+1
        return trades
        
    async def trade_history(self, symbol, start_time, count, batch=1000):
        trades = []
        remained = count
        count = min(remained, batch)
        log.info(f'fetching trade history of length {count} for {symbol} from {start_time}')
        params = {'symbol': symbol.upper(), 'startTime': int(start_time.timestamp()*1000), 'limit': count}
        j = await self.get('aggTrades', params=params)
        for d in j:
            t = self.json_to_trade(d)
            trades.append(t)
        remained -= count
        start_id = trades[-1].id+1
        if remained>0:
            trades += await self.trade_history_from_id(symbol, start_id, remained)
        return trades
        
    ##### end of high-level api
    
    def json_to_candle_restful(self, d):
        return Candle(open_time=datetime.fromtimestamp(d[0]/1000),
            open=Decimal(d[1]), high=Decimal(d[2]), low=Decimal(d[3]), close=Decimal(d[4]),
            volume=Decimal(d[5]), trades=d[8], buy_volume=Decimal(d[9]),
            closed=True, update_time=datetime.fromtimestamp(d[6]/1000))

    def json_to_candle_websocket(self, d):
        return Candle(
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

    def json_to_trade(self, d):
        return Trade(
            id = d['a'],
            time=datetime.fromtimestamp(d['T']/1000),
            price=Decimal(d['p']),
            volume=Decimal(d['q']),
            buy = d['m'],)
        
    def market_stream(self, name):
        return MarketStream(self, name)

    async def get(self, endpoint, params, sign=False):
        async with self.restful_session.get(self.restful_uri+endpoint, params=params) as resp:
            log.debug(f'restful request status: {resp.status}')
            return await resp.json()
    
    ##### end of public api
    
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
                log.debug(f'connecting to market websocket stream of {self} at {uri}')
                self.market_websocket = await websockets.connect(uri)
                asyncio.get_event_loop().create_task(self.market_websocket_task())
            elif len(self.market_streams[name]) == 1:
                log.debug(f'subscribing to market websocket stream of {self} to {name}')
                msg = json.dumps({'method': 'SUBSCRIBE', 'params': [name], 'id': 1})
                await self.market_websocket.send(msg)

    async def close_market_stream(self, stream):
        async with self.market_streams_lock:
            name = stream.name
            if name not in self.market_streams or stream not in self.market_streams[name]:
                log.error(f'stream {name} is not open')
                return
            if self.market_streams_count == 1:
                log.debug(f'disconnecting from market websocket stream of {self}')
                await self.market_websocket.close()
            elif len(self.market_streams[name]) == 1:
                log.debug(f'unsubscribing from market websocket stream of {self} from {name}')
                msg = json.dumps({'method': 'UNSUBSCRIBE', 'params': [name], 'id': 1})
                await self.market_websocket.send(msg)        
            stream_set = self.market_streams[name]
            stream_set.remove(stream)
            self.market_streams_count -= 1

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return self.__str__()
