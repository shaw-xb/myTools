import time, datetime


class MyTools():

    @staticmethod
    def timer(func):
        def inner(*args, **kwargs):
            begin = datetime.datetime.now()
            print(f"{begin}:  The function end.")
            res = func(*args, **kwargs)
            end = datetime.datetime.now()
            print(f"{end}:  The function end.")
            print(f"Total cost : {(end-begin).total_seconds()}")
            return res
        return inner


        
