
class Candle:

    def __init__(self, symbol, timeframe, open_time, update_time, open, high, low, close, volume, buy_volume, trades, closed):
        self.symbol = symbol
        self.timeframe = timeframe
        self.open_time = open_time
        self.update_time = update_time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.buy_volume = buy_volume
        self.trades = trades
        self.closed = closed

    def __str__(self):
        return f'{self.symbol}, {self.timeframe}, t:{self.open_time}, o:{self.open}, h:{self.high}, l:{self.low}, c:{self.close}, v:{self.volume}'

    def __repr__(self):
        return self.__str__()
