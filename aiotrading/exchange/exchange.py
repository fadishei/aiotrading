import logging

log = logging.getLogger('aiotrading')

class Exchange: # abstract exchange (minimum portable) api

    def __init__(self):
        pass
    
    async def open(self):
        log.warning('open: not implemented')
        
    async def close(self):
        log.warning('close: not implemented')

    async def candle_history(self, symbol, timeframe, start_time, count):
        log.error('candle_history: not implemented')

    async def trade_history(self, symbol, start_time, count, start_id=None):
        log.error('trade_history: not implemented')
    
    async def submit_order(self, order):
        log.error('submit_order: not implemented')
    
    async def cancel_order(self, order):
        log.error('cancel_order: not implemented')
    
    async def open_stream(self, stream):
        log.error('open_stream: not implemented')
   
    async def close_stream(self, stream):
        log.warning('close_stream: not implemented')

    async def persist_streams(self, streams):
        log.warning('persist_streams: not implemented')
