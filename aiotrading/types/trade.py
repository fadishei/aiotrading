
class Trade():

    def __init__(self, id, time, price, volume, buy):
        self.id = id
        self.time = time
        self.price = price
        self.volume = volume
        self.buy = buy

    def __str__(self):
        return f'price:{self.price}, volume:{self.volume}'

    def __repr__(self):
        return self.__str__()
