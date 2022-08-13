# Copyright (c) 2021 Viktor Vorobjov
from scrivo.platform import asyncio

from scrivo import logging
log = logging.getLogger("CORE")


def call_try(elog=log.error):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                elog("error: {}".format(e))
                pass
        return applicator
    return decorate


@call_try()
def encode_UTF8(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return data


@call_try()
def decode_UTF8(data):
    if isinstance(data, int):
        return data
    if not isinstance(data, str):
        data = data.decode('utf-8')
    return data


def decode_payload(func):
    def decorator(self, msg):
        if isinstance(msg.payload, bytes):
            msg.payload = msg.payload.decode('utf-8')
        return func(self, msg)
    return decorator


class DataClassArg():
    def __init__(self, *args, **kwargs):
        for key in args:
            setattr(self, key, None)
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def a_dict(self):
        return self.__dict__


async def _g():
    pass
type_coro = type(_g())

0
def is_coro(func):
    if isinstance(func, type_coro):
        return True
    return False


def launch(func, *args, loop=None, **kwargs):

    try:
        res = func(*args, **kwargs)
        if isinstance(res, type_coro):
            if not loop:
                loop = asyncio.get_event_loop()
            return loop.create_task(res)
        else:
            return res
    except Exception as e:
        print(e)
        pass

# scale(10, (0, 100), (80, 30))
def scale(val, src, dst):
    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]

def hexh(data,  sep=' '):
    try:
        data = f'{sep}'.join('{:02x}'.format(x) for x in data)
    except Exception as e:
        log.debug("error: HEX: {}".format(e))
    return data








