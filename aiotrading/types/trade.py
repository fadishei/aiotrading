
class Trade:

    def __init__(self, symbol, id, time, price, volume, buy):
        self.symbol = symbol
        self.id = id
        self.time = time
        self.price = price
        self.volume = volume
        self.buy = buy

    def __str__(self):
        return f'sybol:{self.symbol}, id:{self.id}, time:{self.time}, price:{self.price}, volume:{self.volume}'

    def __repr__(self):
        return self.__str__()
