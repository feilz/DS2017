
from time import time, localtime, strftime


def create_timestamp():
    return int(time())


def ts_to_date(timestamp):
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))
