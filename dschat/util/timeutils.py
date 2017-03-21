
import time
import datetime


def create_timestamp():
    return datetime.datetime.now()


def ts_to_datetime(timestamp):
    return "{:%Y-%m-%d %H:%M:%S}".format(timestamp)


def ts_to_unix(timestamp):
    return int(time.mktime(timestamp.timetuple()))
