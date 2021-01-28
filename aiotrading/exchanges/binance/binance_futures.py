import logging
import asyncio
import json
import time
import hmac
import random
import aiohttp
import websockets
from datetime import datetime, timedelta
from decimal import Decimal
from websockets.exceptions import ConnectionClosedOK
from urllib.parse import urlencode
from ...types import Candle, Trade
from .market_stream import MarketStream
from .candle_stream import CandleStream
from .trade_stream import TradeStream
from .user_stream import UserStream
from .order_update_stream import OrderUpdateStream

log = logging.getLogger('aiotrading')

class BinanceFutures:

    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.name = 'binance-futures'
        self.market_streams = set()
        self.market_streams_lock = asyncio.Lock()
        self.market_streams_connected = set()
        self.market_streams_lock = asyncio.Lock()
        self.user_streams = set()
        self.user_stream_connected = False
        self.user_streams_lock = asyncio.Lock()
        self.websocket_uri = 'wss://fstream.binance.com/'
        self.restful_uri = 'https://fapi.binance.com/fapi/v1/'
        self.restful_limits = {}

    async def open(self):
        log.info(f'connecting to exchange: {self}')
        j = await self.request('exchangeInfo')
        for l in j['rateLimits']:
            if l['intervalNum']==1 and l['interval']=='MINUTE' and l['rateLimitType'] == 'REQUEST_WEIGHT':
                self.restful_limits['X-MBX-USED-WEIGHT-1M'] = (l['limit'], 60)
            elif l['intervalNum']==1 and l['interval']=='MINUTE' and l['rateLimitType'] == 'ORDERS':
                self.restful_limits['X-MBX-ORDER-COUNT-1M'] = (l['limit'], 60)
            else:
                raise Exception(f'unrecognized exchange limit: {l}')
        log.debug('exchange rate limits per second: %s', self.restful_limits)

    async def close(self):
        log.info(f'disconnecting from exchange: {self}')

    async def candle_history(self, symbol, timeframe, start_time, count, batch=1500):
        log.info(f'fetching candle history of length {count} for {symbol}, {timeframe} from {start_time}')
        candles = []
        remained = count
        while remained>0:
            count = min(remained, batch)
            log.debug(f'batch: {start_time}, {count}')
            params = {'symbol': symbol.upper(), 'interval': timeframe, 'startTime': int(start_time.timestamp()*1000), 'limit': count}
            j = await self.request('klines', params=params)
            if len(j) == 0:
                break
            for d in j:
                c = Candle(symbol=symbol, timeframe=timeframe, open_time=datetime.fromtimestamp(d[0]/1000),
                        open=Decimal(d[1]), high=Decimal(d[2]), low=Decimal(d[3]), close=Decimal(d[4]),
                        volume=Decimal(d[5]), trades=d[8], buy_volume=Decimal(d[9]),
                        closed=True, update_time=datetime.fromtimestamp(d[6]/1000)
                    )
                candles.append(c)
            remained -= count
            start_time = candles[-1].open_time+timedelta(minutes=1)
        return candles

    async def trade_history(self, symbol, start_time, count, start_id=None, batch=5):
        log.info(f'fetching trade history of length {count} for {symbol} from {start_time}/{start_id}')
        trades = []
        remained = count
        while remained>0:
            count = min(remained, batch)
            log.debug(f'batch: {start_time}, {count}')
            params = {'symbol': symbol.upper(), 'limit': count}
            if start_id is not None:
                params['fromId'] = start_id
            elif start_time is not None:
                params['startTime'] = int(start_time.timestamp()*1000)
            else:
                raise Exception(f'either start_time or start_id should be specified')
            j = await self.request('aggTrades', params=params)
            if len(j) == 0:
                break
            for d in j:
                t = Trade(
                    symbol = symbol,
                    id = d['a'],
                    time=datetime.fromtimestamp(d['T']/1000),
                    price=Decimal(d['p']),
                    volume=Decimal(d['q']),
                    buy = d['m']
                )
                trades.append(t)
            remained -= count
            start_id = trades[-1].id+1
            start_time = None
        return trades
        
    async def submit_order(self, order):
        order.id = self.gen_rand_id()
        log.info(f'submit order: {order}')
        params = self.order_to_params(order)
        await self.request('order', params=params, method='POST', sign=True)
        #return self.order_update_stream(order)
        
    # TODO: submit_orders

    async def cancel_order(self, order):
        log.info(f'cancel order: {order}')
        params = {
            'symbol': order.symbol,
            'origClientOrderId': order.id
        }
        await self.request('order', params=params, method='DELETE', sign=True)
        # TODO: handle status 400

    def candle_stream(self, symbol, timeframe):
        return CandleStream(self, [(symbol, timeframe)])
        
    def candles_stream(self, candle_specs):
        return CandleStream(self, candle_specs)

    def trade_stream(self, symbol):
        return TradeStream(self, [symbol])
        
    def trades_stream(self, symbols):
        return TradeStream(self, symbols)

    def order_update_stream(self, order):
        return OrderUpdateStream(self, [order])

    def orders_update_stream(self, orders):
        return OrderUpdateStream(self, orders)
        
    def all_orders_update_stream(self):
        return OrderUpdateStream(self, None)
        
# end of portable api

    def market_stream(self, name):
        return MarketStream(self, [name])
    
    def market_streams(self, names):
        return MarketStream(self, names)

    def user_stream(self):
        return UserStream(self)
        
    async def request(self, endpoint, params={}, headers={}, method='GET', sign=False):
        t0 = time.time()
        if sign:
            params['timestamp'] = int(t0*1000)
            params['recvWindow'] = 10000
            qstr = urlencode(params)
            params = {}
            signature = hmac.new(self.api_secret.encode('utf-8'), qstr.encode('utf-8'), 'sha256').hexdigest()
            qstr += '&signature=' + signature
            headers['X-MBX-APIKEY'] = self.api_key
            endpoint += '?' + qstr
        async with aiohttp.request(method, self.restful_uri+endpoint, params=params, headers=headers) as resp:
            if resp.status != 200:
                log.warning(f'restful resp status: {resp.status}')
                log.warning(f'restful resp headers: {resp.headers}')
                text = await resp.text()
                log.warning(f'restful request text: {text}')
                raise
            j = await resp.json()
            waits = []
            for h, (limit, per) in self.restful_limits.items():
                if h in resp.headers:
                    used = float(resp.headers[h])
                    remaining = limit - used
                    wait = per/limit
                    if remaining > limit/2:
                        wait *= 0.5
                    elif remaining < limit/2:
                        wait *= 1.5
                    wait -= (time.time() - t0)
                    log.debug(f'{h} limit: {limit}, remaining: {remaining}, wait: {wait}')
                    if wait<0:
                        wait = 0
                    waits += [wait]
            if len(waits) > 0:
                time.sleep(max(waits))
            elif len(self.restful_limits)>0:
                for h in resp.headers:
                    if h.startswith('X-MBX-'):
                        raise Exception(f'unrecognized rate limit header: {h}')
            return j
            
# end of public api

    def gen_rand_id(self):
        return hex(random.getrandbits(80))[2:]

    def order_to_params(self, order):
        params = {
            'symbol': order.symbol.upper(),
            'side': order.side.upper(),
            'quantity': str(order.size),
            'newClientOrderId': order.id
        }
        if order.type == 'limit':
            if order.stop_price is None:
                params['timeInForce'] = 'GTX' if order.post_only else 'GTC'
                params['price'] = str(order.price)
                params['type'] = 'LIMIT'
            else:
                params['price'] = str(order.price)
                params['stopPrice'] = str(order.stop_price)
                params['type'] = 'STOP'
        elif order.type == 'market':
            if order.stop_price is None:
                params['type'] = 'MARKET'
            else:
                params['stopPrice'] = str(order.stop_price)
                params['type'] = 'STOP_MARKET'
        if order.reduce_only:
            params['reduceOnly'] = True
        #log.info(f'params:\n{params}')
        return params
        
    async def websocket_rate_limit(self, t0):
        t = 0.1-(time.time()-t0)
        if t>0:
            await asyncio.sleep(0.1)
    
    async def market_websocket_connect(self):
        log.debug(f'connecting to market websocket stream')
        t0 = time.time()
        self.market_websocket = await websockets.connect(f'{self.websocket_uri}stream')
        await self.websocket_rate_limit(t0)
        asyncio.get_event_loop().create_task(self.market_websocket_task())

    async def market_websocket_disconnect(self):
        log.debug(f'disconnecting from market websocket stream')
        await self.market_websocket.close()

    async def market_websocket_task(self):
        log.debug('starting market websocket task')
        while True:
            try:
                msg = await self.market_websocket.recv()
            except ConnectionClosedOK:
                break
            j = json.loads(msg)
            for stream in self.market_streams:
                if 'stream' in j:
                    await stream.write(j)
        log.debug('market websocket task stopped')
        
    async def user_websocket_connect(self):
        log.debug(f'connecting to user websocket stream')
        listen_key = await self.user_websocket_create_key()
        t0 = time.time()
        self.user_websocket = await websockets.connect(f'{self.websocket_uri}ws/{listen_key}')
        await self.websocket_rate_limit(t0)
        asyncio.get_event_loop().create_task(self.user_websocket_task())

    async def user_websocket_disconnect(self):
        log.debug(f'disconnecting from user websocket stream')
        await self.user_websocket.close()
        await self.user_websocket_delete_key()
        
    async def user_websocket_task(self):
        log.debug('starting user websocket task')
        keepalive_task = asyncio.get_event_loop().create_task(self.user_websocket_keepalive_task())
        while True:
            try:
                msg = await self.user_websocket.recv()
            except ConnectionClosedOK:
                break
            j = json.loads(msg)
            for stream in self.user_streams:
                await stream.write(j)
        keepalive_task.cancel()
        log.debug('user websocket task stopped')

    async def user_websocket_keepalive_task(self):
        log.debug('starting user websocket keepalive task')
        while True:
            try:
                await asyncio.sleep(45*60)
                await self.user_websocket_refresh_key()
            except asyncio.CancelledError:
                break
        log.debug('user websocket keepalive task stopped')

    async def user_websocket_create_key(self):
        log.debug('creating user websocket listen key')
        j = await self.request('listenKey', method='POST', sign=True)
        return j['listenKey']

    async def user_websocket_delete_key(self):
        log.debug('deleting user websocket listen key')
        await self.request('listenKey', method='DELETE', sign=True)

    async def user_websocket_refresh_key(self):
        log.debug('refreshing user websocket listen key')
        await self.request('listenKey', method='PUT', sign=True)
        
    async def open_market_stream(self, stream):
        log.info(f'opening {stream}')
        async with self.market_streams_lock:
            if len(self.market_streams_connected)==0:
                await self.market_websocket_connect()
            self.market_streams.add(stream)
            tgt = stream.names-self.market_streams_connected
            if len(tgt)>0:
                s = ','.join(tgt)
                log.debug(f'subscribing to market websocket stream(s): {s}')
                msg = json.dumps({'method': 'SUBSCRIBE', 'params': list(tgt), 'id': 1})
                t0 = time.time()
                await self.market_websocket.send(msg)
                await self.websocket_rate_limit(t0)
                self.market_streams_connected = self.market_streams_connected.union(tgt)

    async def open_user_stream(self, stream):
        log.info(f'opening {stream}')
        async with self.user_streams_lock:
            if not self.user_stream_connected:
                await self.user_websocket_connect()
                self.user_stream_connected = True
            self.user_streams.add(stream)

    async def close_market_stream(self, stream):
        log.info(f'closing {stream}')
        async with self.market_streams_lock:
            if stream not in self.market_streams:
                log.error(f'{stream} is not open')
                return
            if not stream.persistent:
                s = ','.join(stream.names)
                log.debug(f'unsubscribing from market websocket stream(s): {s}')
                msg = json.dumps({'method': 'UNSUBSCRIBE', 'params': list(stream.names), 'id': 1})
                t0 = time.time()
                await self.market_websocket.send(msg)
                await self.websocket_rate_limit(t0)
                self.market_streams_connected -= stream.names
                if len(self.market_streams_connected)==0:
                    await self.market_websocket_disconnect()
            self.market_streams.remove(stream)

    async def close_user_stream(self, stream):
        log.debug(f'closing {stream}')
        async with self.user_streams_lock:
            if stream not in self.user_streams:
                log.error(f'{stream} is not open')
                return
            if not stream.persistent and self.user_stream_connected:
                await self.user_websocket_disconnect()
                self.user_stream_connected = False
            self.user_streams.remove(stream)

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return self.__str__()
