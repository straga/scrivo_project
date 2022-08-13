# Copyright (c) 2021 Viktor Vorobjov

from scrivo.tools.tool import is_coro
from scrivo.dev import asyncio


from scrivo import logging
log = logging.getLogger("MBUS")


class RpcEnv:
    def __init__(self, core):
        self.core = core

    @staticmethod
    def isgenerator(iterable):
        return hasattr(iterable, '__iter__') and not hasattr(iterable, '__len__')

    class IsClass(object):
        pass


    '''
    Search method or arg in env by nema and path
    env_name = "mqtt"
    path = "client.status" / disconect
    '''
    def path(self, env_name, path):
        env_call = self.core.env.get(env_name)
        for _attr in path.split("."):
            if len(_attr):
                env_call = getattr(env_call, _attr)
        return env_call


    '''
    call path, check callable/asyncio_coro or return arg value
    '''
    @staticmethod
    async def call(path,  *args, **kwargs):
        if callable(path):
            call_func = path(*args, **kwargs)
            if is_coro(call_func):
                path = await call_func
            else:
                path = call_func
        return path


    '''
    Call from env and path some and return result
    '''
    async def action(self, env_name, path, args, kwargs, will_yield=False):

        path = self.path(env_name, path)
        result = await self.call(path, *args, **kwargs)
        if result and will_yield and self.isgenerator(result):
            return list(result)
        return result


    '''
    Return List(State) of env/path
    '''
    def state(self, env_name, path="", attr=None):
        path = self.path(env_name, path)
        state = {}
        for k in attr:
            val = getattr(path, k, None)
            if isinstance(val, (float, int, str, list, tuple)):
                state[k] = val
            else:
                state[k] = type(val).__name__

        return state
