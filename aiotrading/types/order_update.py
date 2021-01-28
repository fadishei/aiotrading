import random

# status: submit, cancel, partial, fill, expire

class OrderUpdate:

    last_id = 0

    def __init__(self, order, time, status, size, total_size, price, average_price):
        self.order = order
        self.time = time
        self.status = status
        self.size = size
        self.total_size = total_size
        self.price = price
        self.average_price = average_price
        
    def __str__(self):
        return f'id: {self.order.id}, t: {self.time}, status: {self.status}, size:{self.size}'

    def __repr__(self):
        return self.__str__()
