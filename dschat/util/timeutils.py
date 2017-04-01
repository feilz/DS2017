
import time


def create_timestamp():
    return int(time.time())


def ts_to_date(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
