# Copyright (c) Viktor Vorobjov

from scrivo.rpc import jsonrpc
from scrivo import logging

log = logging.getLogger("CORE")


class Core:
    __slots__ = ('__dict__', 'env', 'mbus', 'uconf')
    _core = None

    def __init__(self, mbus, uconf):
        Core._core = self
        self.mbus = mbus
        self.mbus.activate(core=self)
        self.uconf = uconf
        self.part_name = "."
        self.env = {}
        self.rpc = jsonrpc.JsonRpc(core=self, mbus=self.mbus)
        self.action_list = []

    def env_set(self, name, action, *args, **kwargs):

        if self.env.get(name):
            log.error("Env: {} - Already Exist".format(name))
        else:
            self.env[name] = action(name, *args, **kwargs)


    @staticmethod
    def get_core():
        return Core._core

