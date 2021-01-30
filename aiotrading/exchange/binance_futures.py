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
from collections import defaultdict
from websockets.exceptions import ConnectionClosedOK
from urllib.parse import urlencode
from .exchange import Exchange
from .. import Candle, Trade, Order, OrderUpdate, CandleStream, TradeStream, OrderUpdateStream

log = logging.getLogger('aiotrading')

class BinanceFutures(Exchange):

    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.name = 'binance-futures'
        self.rest_uri = 'https://fapi.binance.com/fapi/v1/'
        self.rest_limits = {}
        self.ws_uri = 'wss://fstream.binance.com/'
        self.ws_lock = asyncio.Lock()
        self.mws_streams = defaultdict(set)
        self.mws_connected = set() 
        self.mws_persisted = set()
        self.uws_streams = set()
        self.uws_connected = False
        self.uws_persisted = False
        self.orders = {}
        
    async def open(self):
        log.info(f'connecting to exchange: {self}')
        j = await self.request('exchangeInfo')
        self.symbols = {d['symbol']: d for d in j['symbols'] if d['status']=='TRADING'}
        log.debug(f'exchange has {len(self.symbols)} symbols')
        for l in j['rateLimits']:
            if l['intervalNum']==1 and l['interval']=='MINUTE' and l['rateLimitType'] == 'REQUEST_WEIGHT':
                self.rest_limits['X-MBX-USED-WEIGHT-1M'] = (l['limit'], 60)
            elif l['intervalNum']==1 and l['interval']=='MINUTE' and l['rateLimitType'] == 'ORDERS':
                self.rest_limits['X-MBX-ORDER-COUNT-1M'] = (l['limit'], 60)
            else:
                raise Exception(f'unrecognized exchange limit: {l}')
        log.debug('exchange rate limits per second: %s', self.rest_limits)

    async def close(self):
        log.info(f'disconnecting from exchange: {self}')

    async def candle_history(self, symbol, timeframe, start_time, count):
        batch = 1500
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

    async def trade_history(self, symbol, start_time, count, start_id=None):
        batch = 1000
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
        self.orders[order.id] = order
        params = self.get_order_params(order)
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

    async def persist_streams(self, streams):
        log.info(f'persisting streams {streams}')
        m = []
        u = False
        for stream in streams:
            if isinstance(stream, (CandleStream, TradeStream)):
                m.append(self.mws_get_endpoint(stream))
            elif isinstance(stream, (OrderUpdateStream,)):
                u = True
            else:
                log.error(f'invalid stream type {type(stream)}')
        async with self.ws_lock:
            if len(m)>0:
                await self.mws_persist(m)
            if u:
                await self.uws_persist()

# end of portable api

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
        async with aiohttp.request(method, self.rest_uri+endpoint, params=params, headers=headers) as resp:
            if resp.status != 200:
                log.warning(f'rest resp status: {resp.status}')
                log.warning(f'rest resp headers: {resp.headers}')
                text = await resp.text()
                log.warning(f'rest request text: {text}')
                raise
            j = await resp.json()
            waits = []
            for h, (limit, per) in self.rest_limits.items():
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
            elif len(self.rest_limits)>0:
                for h in resp.headers:
                    if h.startswith('X-MBX-'):
                        raise Exception(f'unrecognized rate limit header: {h}')
            return j
            
# end of public api

    async def open_stream(self, stream):
        log.info(f'opening {stream}')
        if isinstance(stream, (CandleStream, TradeStream)):
            async with self.ws_lock:
                await self.mws_open(stream)
        elif isinstance(stream, (OrderUpdateStream,)):
            async with self.ws_lock:
                await self.uws_open(stream)
        else:
            log.error(f'invalid stream type {type(stream)}')
        
    async def close_stream(self, stream):
        log.info(f'closing {stream}')
        if isinstance(stream, (CandleStream, TradeStream)):
            async with self.ws_lock:
                await self.mws_close(stream)
        elif isinstance(stream, (OrderUpdateStream,)):
            async with self.ws_lock:
                await self.uws_close(stream)
        else:
            log.error(f'invalid stream type {type(stream)}')
        
    async def mws_connect(self, endpoints):
        log.debug(f'connecting to market websocket endpoints {endpoints}')
        tgt = set(endpoints)-self.mws_connected
        if len(tgt)>0:
            t0 = time.time()
            if len(self.mws_connected)==0:
                uri = f'{self.ws_uri}stream?streams=' + '/'.join(tgt)
                self.mws = await websockets.connect(uri)
                self.mws_task = asyncio.get_event_loop().create_task(self.mws_worker())
            else:
                msg = json.dumps({'method': 'SUBSCRIBE', 'params': list(tgt), 'id': 1})
                await self.mws.send(msg)
            await self.ws_rate_limit(t0)
            self.mws_connected = self.mws_connected.union(tgt)

    async def uws_connect(self):
        log.debug(f'connecting to user websocket')
        if not self.uws_connected:
            t0 = time.time()
            listen_key = await self.uws_create_key()
            self.uws = await websockets.connect(f'{self.ws_uri}ws/{listen_key}')
            await self.ws_rate_limit(t0)
            self.uws_connected = True
            self.uws_task = asyncio.get_event_loop().create_task(self.uws_worker())

    async def mws_disconnect(self, endpoints):
        log.debug(f'disconnecting from market websocket endpoints {endpoints}')
        tgt = set(endpoints)-self.mws_persisted
        if len(tgt)>0:
            t0 = time.time()  
            if tgt == self.mws_connected:
                await self.mws.close()
                self.mws_task.cancel()
                try:
                    await self.mws_task
                except asyncio.CancelledError:
                    pass
            else:
                msg = json.dumps({'method': 'UNSUBSCRIBE', 'params': list(tgt), 'id': 1})
                await self.mws.send(msg)
            await self.ws_rate_limit(t0)
            self.mws_connected -= tgt

    async def uws_disconnect(self):
        log.debug(f'disconnecting from user websocket')
        if self.uws_connected and not self.uws_persisted:
            t0 = time.time()  
            await self.uws.close()
            self.uws_task.cancel()
            try:
                await self.uws_task
            except asyncio.CancelledError:
                pass
            await self.uws_delete_key()
            await self.ws_rate_limit(t0)
            self.uws_connected = False
            
    async def mws_persist(self, endpoints):
        log.debug(f'persisting market websocket endpoints {endpoints}')
        await self.mws_connect(endpoints)
        self.mws_persisted = self.mws_persisted.union(set(endpoints))

    async def uws_persist(self):
        log.debug(f'persisting user websocket')
        await self.uws_connect()
        self.uws_persisted = True

    def mws_get_endpoint(self, stream):
        if isinstance(stream, CandleStream):
            return f'{stream.symbol}@kline_{stream.timeframe}'
        if isinstance(stream, TradeStream):
            return f'{stream.symbol}@aggTrade'
        raise Exception(f'invalid stream type {type(stream)}')
        
    def mws_parse_message(self, msg):
        if 'stream' in msg:
            d = msg['data']
            if d['e'] == 'kline':
                return Candle(
                    symbol = d['s'].lower(),
                    timeframe = d['k']['i'],
                    open_time=datetime.fromtimestamp(d['k']['t']/1000),
                    update_time=datetime.fromtimestamp(d['k']['T']/1000), #?d['E']
                    open=Decimal(d['k']['o']),
                    high=Decimal(d['k']['h']),
                    low=Decimal(d['k']['l']),
                    close=Decimal(d['k']['c']),
                    volume=Decimal(d['k']['v']),
                    buy_volume = Decimal(d['k']['V']),
                    trades=int(d['k']['n']),
                    closed=d['k']['x'])
            if d['e'] == 'aggTrade':
                return Trade(
                    symbol = d['s'].lower(),
                    id = d['a'],
                    time=datetime.fromtimestamp(d['T']/1000),
                    price=Decimal(d['p']),
                    volume=Decimal(d['q']),
                    buy = d['m']
                )
        return None

    def uws_parse_message(self, msg):
        if 'e' in msg and msg['e'] == 'ORDER_TRADE_UPDATE':
            d = msg['o']
            if d['c'] in self.orders:
                return OrderUpdate(
                        order=self.orders[d['c']],
                        time=datetime.fromtimestamp(msg['T']/1000),
                        status=self.get_order_status(d['X']),
                        size=Decimal(d['l']),
                        total_size=Decimal(d['z']),
                        price=Decimal(d['L']),
                        average_price=Decimal(d['ap']),
                    )
        return None

    async def mws_open(self, stream):
        log.debug(f'opening market stream {stream}')
        endpoint = self.mws_get_endpoint(stream)
        await self.mws_connect([endpoint])
        self.mws_streams[endpoint].add(stream)

    async def uws_open(self, stream):
        log.debug(f'opening user stream {stream}')
        await self.uws_connect()
        self.uws_streams.add(stream)

    async def mws_close(self, stream):
        log.debug(f'closing market stream {stream}')
        endpoint = self.mws_get_endpoint(stream)
        if endpoint not in self.mws_streams:
            log.warning(f'{stream} is not open')
            return
        await self.mws_disconnect([endpoint])
        self.mws_streams[endpoint].remove(stream)

    async def uws_close(self, stream):
        log.debug(f'closing user stream {stream}')
        if stream not in self.uws_streams:
            log.warning(f'{stream} is not open')
            return
        await self.uws_disconnect()
        self.uws_streams.remove(stream)
        
    async def mws_worker(self):
        log.debug('starting market websocket task')
        while True:
            try:
                msg = await self.mws.recv()
            except ConnectionClosedOK:
                break
            j = json.loads(msg)
            item = self.mws_parse_message(j)
            if item is not None:
                async with self.ws_lock:
                    streams = self.mws_streams[j['stream']]
                    for stream in streams:
                        if isinstance(stream, CandleStream) and isinstance(item, Candle):
                            await stream.write(item)
                        elif isinstance(stream, TradeStream) and isinstance(item, Trade):
                            await stream.write(item)
        log.debug('market websocket task stopped')
        
    async def uws_worker(self):
        log.debug('starting user websocket task')
        keepalive_task = asyncio.get_event_loop().create_task(self.uws_keepalive_worker())
        while True:
            try:
                msg = await self.uws.recv()
            except ConnectionClosedOK:
                break
            async with self.ws_lock:
                item = self.uws_parse_message(json.loads(msg))
                if item is not None:
                    for stream in self.uws_streams:
                        if isinstance(stream, OrderUpdateStream) and isinstance(item, OrderUpdate) and stream.order.id==item.order.id:
                            await stream.write(item)
                            if item.status in ['fill', 'cancel', 'expire']:
                                self.orders.pop(item.order.id)
        keepalive_task.cancel()
        log.debug('user websocket task stopped')

    async def uws_keepalive_worker(self):
        log.debug('starting user websocket keepalive task')
        while True:
            try:
                await asyncio.sleep(45*60)
                await self.uws_refresh_key()
            except asyncio.CancelledError:
                break
        log.debug('user websocket keepalive task stopped')

    async def uws_create_key(self):
        log.debug('creating user websocket listen key')
        j = await self.request('listenKey', method='POST', sign=True)
        return j['listenKey']

    async def uws_delete_key(self):
        log.debug('deleting user websocket listen key')
        await self.request('listenKey', method='DELETE', sign=True)

    async def uws_refresh_key(self):
        log.debug('refreshing user websocket listen key')
        await self.request('listenKey', method='PUT', sign=True)

    async def ws_rate_limit(self, t0):
        t = 0.1-(time.time()-t0)
        if t>0:
            await asyncio.sleep(0.1)
    
    def gen_rand_id(self):
        return hex(random.getrandbits(80))[2:]

    def get_order_params(self, order):
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

    def get_order_status(self, s):
        if s == 'NEW':
            return 'submit'
        elif s == 'PARTIALLY_FILLED':
            return 'partial'
        elif s == 'FILLED':
            return 'fill'
        elif s == 'CANCELED':
            return 'cancel'
        elif s == 'EXPIRED':
            return 'expire'
        else:
            return s

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return self.__str__()
