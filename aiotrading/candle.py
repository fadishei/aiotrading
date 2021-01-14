
class Candle():

    def __init__(self, open_time, update_time, open, high, low, close, volume, buy_volume, trades, closed):
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
        return f'o:{self.open}, h:{self.high}, l:{self.low}, c:{self.close}, v:{self.volume}'

    def __repr__(self):
        return self.__str__()
