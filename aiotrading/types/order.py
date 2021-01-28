# stop orders are known as having stop_price=None (not from type):
# type  side  stop
# limit buy   none
# market buy  none
# limit buy   yes
# market buy  yes

# status: submit, cancel, partial, fill

class Order:
    
    def __init__(self, symbol, type, side, size, price=None, stop_price=None, reduce_only=False, post_only=False, id=None):
        self.symbol = symbol
        self.type = type
        self.side = side
        self.size = size
        self.price = price
        self.stop_price = stop_price
        self.reduce_only = reduce_only
        self.post_only = post_only
        self.id = id

    def __str__(self):
        return f'id:{self.id}, symbol:{self.symbol}, type:{self.type}, side:{self.side}, price:{self.price}, size:{self.size},  stop_price:{self.stop_price}'

    def __repr__(self):
        return self.__str__()
