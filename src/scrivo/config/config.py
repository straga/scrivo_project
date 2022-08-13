# Copyright (c) 2021 Viktor Vorobjov

import json
from collections import OrderedDict
from scrivo.config import json_store as uorm
from scrivo.dev import asyncio

from scrivo import logging
log = logging.getLogger("CONF")


class ConfigManager():
    # __slots__ = ('__dict__', 'db', '_tbl', '_sch')

    def __init__(self, store_path="u_config"):

        _sch_name = "_schema"
        _sch_conf = OrderedDict([
            ("name", ("str", "")),
            ("sch", ("dict", ())),
        ])

        self.store = uorm.Store(store_schema=_sch_name, store_path=store_path, store_config=_sch_conf)
        self.lock = asyncio.Lock()

    def store_init(self, schema_name):
        store = self.store.get_store(schema_name)
        store.schema_init()
        return store

    # write data from ...
    def from_dict(self, sch, name, data, upd=True):
        data["name"] = name
        data["_schema"] = sch
        data["_upd"] = upd
        return self.save_data(data)

    def from_string(self, json_string):
        error = False
        try:
            json_data = json.loads(json_string)
        except Exception as e:
            log.error("Error: from string: {}".format(e))
            return "error:{}".format(e)

        for data in json_data.values():
            error = self.save_data(data)
            if error:
                break
        return error

    def from_file(self, file):
        for data in self.store.from_file(file).values():
            self.save_data(data)

    # save
    def save_data(self, data):
        if "_schema" in data:
            log.debug("SCHEMA DATA: {}".format(data["_schema"]))

            store = self.store_init(data["_schema"])
            return store.write(data)

    # select
    @staticmethod
    def generate_list(generator):
        _list = []
        for res in generator:
            _list.append(res)
        return _list

    def model(self, sch_name, result):
        if result:
            return ObjModel(result, _schema=sch_name, _config=self)

    def select_one(self, sch_name, cfg_name="default", model=False):
        store = self.store_init(sch_name)
        result = store.select_one(cfg_name)
        if model:
            result = self.model(sch_name, result)
        return result

    def select(self, sch_name, rtype="list", **kwargs):
        store = self.store_init(sch_name)

        if rtype == "list":
            return self.generate_list(store.select(**kwargs))

        elif rtype == "model":
            # first in where
            for res in store.select(**kwargs):
                return self.model(sch_name, res)

    # scan
    def scan_name(self, sch_name):
        store = self.store_init(sch_name)
        return self.generate_list(store.scan_name())

    def scan(self, sch_name):
        store = self.store_init(sch_name)
        return store.scan()

    # delete
    def delete(self, sch, where):
        store = self.store_init(sch)
        return store.delete(where)

    # Control
    def _call_cmd(self, method, param, *args, **kwargs):

        result = None
        if hasattr(self, method):

            try:
                func = getattr(self, method)
                result = func(param, *args, **kwargs)

            except Exception as e:
                result = ("CMD_ERROR : err:{}, method:{}, param:{}, arg:{}, kwg:{}".format(e, method, param, args, kwargs))
                log.error(result)
                pass

        return result

    async def call(self, method, param, *args, **kwargs):
        async with self.lock:
            result = self._call_cmd(method, param, *args, **kwargs)
            #result = await run_in_executer(self._call_cmd, method, param, *args, **kwargs)
        return result


class ObjModel:

    def __init__(self, *args, **kwargs):
        self._schema = None
        self._config = None

        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

    async def update(self):
        if self._schema and self._config:
            self._upd = True
            await self._config.call("save_data", self.__dict__.copy())

    # def __repr__(self):
    #     return self.__dict__


