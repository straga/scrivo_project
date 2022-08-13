from scrivo import logging
log = logging.getLogger("core")
log.setLevel(logging.INFO)

from time import ticks_ms

import uasyncio as asyncio
from uasyncio import Lock
from uasyncio import Event
from primitives.queue import Queue


#upy
async def _awrite(writer, data,  b=False):

    try:
        if isinstance(data, str):
            data = data.encode('utf-8')
        await writer.awrite(data)
    except Exception as e:
        log.debug("Error: write: {}".format(e))
        pass


async def _aclose(writer):
    try:
        await writer.aclose()
    except Exception as e:
        log.debug("close: {}".format(e))
        pass


def _try_alloc_byte_array(size):
    import gc
    for x in range(10):
        try:
            gc.collect()
            return bytearray(size)
        except:
            log.debug("Error alloc byte ")
            pass
    return None


def _buffer(default=64):
    return _try_alloc_byte_array(default)


async def _buffer_writer(awrite, writer, buf, x):

    try:
        await writer.awrite(buf, 0, x)
    except Exception as err:
        log.error("BUF:{}".format(err))
        pass





