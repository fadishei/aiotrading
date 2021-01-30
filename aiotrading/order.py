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
        return f'order id:{self.id}, symbol:{self.symbol}, type:{self.type}, side:{self.side}, price:{self.price}, size:{self.size},  stop_price:{self.stop_price}'

    def __repr__(self):
        return self.__str__()

class OrderUpdate:

    last_id = 0

    def __init__(self, order, time, status, size, total_size, price, average_price):
        self.order = order
        self.time = time
        self.status = status # submit, cancel, partial, fill, expire
        self.size = size
        self.total_size = total_size
        self.price = price
        self.average_price = average_price
        
    def __str__(self):
        return f'order update id:{self.order.id}, t:{self.time}, status:{self.status}, price:{self.price}, size:{self.size}'

    def __repr__(self):
        return self.__str__()
