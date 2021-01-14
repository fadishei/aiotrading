import logging
import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosedOK
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
from .exchange import Exchange
from ..candle import Candle
from ..candle_stream import CandleStream

log = logging.getLogger('aiotrading')

class BinanceFutures(Exchange):

    def __init__(self):
        self.candle_streams = defaultdict(set)
    
    async def connect(self):
        log.info(f'connecting to exchange')
        self.market_ws = await websockets.connect('wss://fstream.binance.com/stream/')
        asyncio.get_event_loop().create_task(self.market_worker())

    async def disconnect(self):
        log.info('disconnecting from exchange')
        await self.market_ws.close()

    async def market_worker(self):
        while True:
            try:
                s = await self.market_ws.recv()
            except ConnectionClosedOK:
                return
            j = json.loads(s)
            if 'stream' in j:
                d = j['data']
                symbol = d['s'].lower()
                timeframe = d['k']['i']
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
                for candle_stream in self.candle_streams[symbol, timeframe]:
                    await candle_stream.queue.put(c)

    async def open_candle_stream(self, symbol, timeframe):
        log.info(f'opening candle stream {symbol}@{timeframe}')
        s = self.candle_streams[symbol, timeframe]
        if len(s) == 0:
            log.info(f'subscribing to websocket for {symbol}@{timeframe}')
            msg = json.dumps({'method': 'SUBSCRIBE', 'params': [f'{symbol}@kline_{timeframe}'], 'id': 1})
            await self.market_ws.send(msg)
        cs = CandleStream(self, symbol, timeframe)
        s.add(cs)
        return cs

    async def close_candle_stream(self, candle_stream):
        symbol, timeframe = candle_stream.symbol, candle_stream.timeframe
        log.info(f'closing candle stream {symbol}@{timeframe}')
        s = self.candle_streams[symbol, timeframe]
        s.remove(candle_stream)
        if len(s) == 0:
            log.info(f'unsubscribing from websocket for {symbol}@{timeframe}')
            msg = json.dumps({'method': 'UNSUBSCRIBE', 'params': [f'{symbol}@kline_{timeframe}'], 'id': 1})
            await self.market_ws.send(msg)
        
        