
# ESP32
import asyncio
# Queue from asyncio becouse micropython does not have Queue, use Queue from primitives
from primitives.queue import Queue

from time import ticks_ms, ticks_diff

import gc
import os

from scrivo import logging
log = logging.getLogger("core")
# log.setLevel(logging.INFO)

#upy
async def awrite(writer, data,  b=False):

    try:
        if isinstance(data, str):
            data = data.encode('utf-8')
        await writer.awrite(data)
    except Exception as e:
        log.debug("Error: write: {}".format(e))
        pass


async def aclose(writer):
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


def buffer(default=64):
    return _try_alloc_byte_array(default)

async def buffer_awriter(writer, buf, x):
    try:
        await writer.awrite(buf, 0, x)
    except Exception as err:
        log.error("BUF:{}".format(err))
        pass
buffer_writer = buffer_awriter

# asyncio for micropython check about task exception and done task
async def _g():
    pass
type_coro = type(_g())

def is_coro(func):
    if isinstance(func, type_coro):
        return True
    return False

# # Generator type
# type_gen = type((lambda: (yield))())
#
# # Generator function type
# type_genf = type((lambda: (yield)))


# def is_coro(func):
#     if isinstance(func, type_gen):
#         return True
#     return False
#
# def is_corof(func):
#     if isinstance(func, type_genf):
#         return True
#     return False

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

# import scrivo.core as core
# def launch(func, *args, loop=None, **kwargs):
#     try:
#         res = func(*args, **kwargs)
#         if isinstance(res, type_coro):
#             if not loop:
#                 loop = asyncio.get_event_loop()
#             task = loop.create_task(res)
#             if core.tasks_log:
#                 core.tasks.append(task)
#             return task
#         else:
#             return res
#     except Exception as e:
#         print(e)

def uname():
    return list(os.uname())

def mem_info():
    #gc.collect()
    return [gc.mem_free(), gc.mem_alloc()]
