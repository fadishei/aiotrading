import asyncio
import logging
from aiotrading import CandleStream, TradeStream, MixedStream
from aiotrading.exchange import BinanceFutures

log = logging.getLogger('aiotrading')

async def main():
    async with BinanceFutures() as exchange:
        streams = [CandleStream(exchange, 'btcusdt', '1h'), TradeStream(exchange, 'ltcusdt')]
        await exchange.persist_streams(streams)
        async with MixedStream(streams) as stream:
            for i in range(20):
                substream, data = await stream.read()
                log.info(f'{substream}: {data}')
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.get_event_loop().run_until_complete(main())