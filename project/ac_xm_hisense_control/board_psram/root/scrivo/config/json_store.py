# Copyright (c) 2020 Viktor Vorobjov
import os
from collections import OrderedDict
import json
from scrivo.u_os import isdir
from scrivo.u_os import isfile

import builtins

# Run in executer
# from core.thread.thread import run_in_executer
# result = await run_in_executer(self._call_cmd, method, param, *args, **kwargs)

from scrivo import logging
log = logging.getLogger("FJSON")


class Store:
    __store__ = "./store"
    __schema__ = ""
    __config__ = []

    def __init__(self, schema=None, store_path=None, store_config=None, store_schema=None):

        self.schema = schema
        self.config = None

        if store_path:
            Store.__store__ = store_path

        if store_config:
            Store.__config__ = store_config

        if store_schema:
            Store.__schema__ = store_schema
            self.schema = store_schema

        # store directory
        self.store_location()
        # store schema directory
        self.schema_location()

    def schema_init(self):

        self.config = None
        if self.schema == Store.__schema__:
            self.config = Store.__config__
        else:
            sch_obj = self.select_one(self.schema, schema=True)
            if sch_obj:
                self.config = OrderedDict(sch_obj["sch"])
                self.schema_location()

    @classmethod
    def get_store(cls, name):
        return cls(schema=name)

    @classmethod
    def path_to_store(cls):
        return "{}".format(cls.__store__)

    def path_to_schema(self):
        return "{}/{}".format(self.__store__, self.schema)

    def path_to_data(self, data, schema=False):
        if schema:
            schema = self.__schema__
        else:
            schema = self.schema
        return "{}/{}/{}".format(self.__store__, schema, data)

    @classmethod
    def list_dir(cls, path):
        try:
            return os.listdir(path)
        except OSError as e:
            log.debug("LSDIR: {}".format(e))
            return None

    @classmethod
    def create_dir(cls, name):
        try:
            os.mkdir(name)
        except OSError as e:
            log.debug("MKDIR: {}, {}".format(e, name))
            return False
        log.info("MKDIR: {}".format(name))
        return True

    @classmethod
    def store_location(cls):
        _path = cls.path_to_store()
        if not isdir(_path):
            cls.create_dir(_path)

    def schema_location(self):
        _path = self.path_to_schema()
        if not isdir(_path):
            self.create_dir(_path)

    def validate(self, cfg):
        error = False
        remove = [k for k in cfg.keys() if k.startswith("_")]

        for k in remove:
            del cfg[k]

        for key, val in self.config.items():
            _type = getattr(builtins, val[0])

            if key not in cfg:
                cfg[key] = self.default(val[1])

            elif type(cfg[key]) != _type and not callable(val[1]):

                try:
                    if val[0] == "bool":
                        cfg[key] = self.str2bool(cfg[key])
                    else:
                        cfg[key] = _type(cfg[key])
                except Exception as e:
                    log.error("VALIDATE: {}, k: {}, d: {}".format(e, key, cfg))
                    cfg[key] = self.default(val[1])
                    error = "error:{},{}".format(e, key)
                    break

            cfg[key] = self.secret(cfg[key])
        log.debug("VALIDATE: OK")
        return error

    @staticmethod
    def from_file(file):
        result = {}
        if isfile(file):
            with open(file) as f:
                try:
                    fc = f.read()
                    result = json.loads(fc)
                except Exception as e:
                    log.error("Error: from file: {} - {}".format(file, e, ))
                    pass
        return result

    def write(self, config):

        error = False
        if "name" in config:
            _name = config["name"]
            _upd = None
            if "_upd" in config:
                _upd = config["_upd"]

            mode = False
            is_file = isfile(self.path_to_data(_name))

            if not is_file:
                mode = "w"
            elif _upd:
                mode = "w+"
                new_config = self.select_one(_name)
                if new_config:
                    del config["name"]
                    new_config.update(config)
                    config = new_config

            if _upd is not None and not _upd:
                mode = False

            log.debug("Open Mode: {},  path:{}".format(mode, self.path_to_data(_name)))

            if mode:
                error = self.validate(config)
                if not error:
                    file = self.path_to_data(_name)
                    log.debug("fullpath: {}".format(file))

                    data = json.dumps(config)
                    log.debug("Data dump !")

                    with open(file, mode) as f:
                        log.debug("File Opened !")
                        f.write(data)
                # log.info("+")
        return error

    @staticmethod
    def default(default):
        if callable(default):
            default = default()
        return default

    @staticmethod
    def str2bool(val):
        return val.lower() in ("yes", "true", "1")

    @staticmethod
    def secret(val):
        secret = "!secret "
        if isinstance(val, str) and val.startswith(secret):
            val = val.split(secret, 1)[-1]

            try:
                with open("./secret") as f:
                    for line in f:
                        if line.startswith(val):
                            val = line.split(":")[-1].rstrip()
            except Exception as e:
                log.error("Error: secret file: {}".format(e))
                pass

        return val

    # select
    def select_one(self, name, schema=False):
        file = self.path_to_data(name, schema=schema)
        if isfile(file):
            with open(file) as f:
                data = f.read()
                if data:
                    return json.loads(data)

    def select(self, **fields):
        for cfg_name in self.list_dir(self.path_to_schema()):
            with open(self.path_to_data(cfg_name)) as f:
                f_cfg = f.read()
                if f_cfg:
                    row = json.loads(f_cfg)
                    for key in self.config:
                        if key in fields and key in row:
                            if row[key] == fields[key]:
                                yield row

    # scan
    def scan(self):
        _list = []
        for cfg_name in self.list_dir(self.path_to_schema()):
            _list.append(self.select_one(cfg_name))
        return _list

    @classmethod
    def scan_store(cls):
        for file_name in cls.list_dir(cls.path_to_store()):
            yield file_name

    def scan_name(self):
        for file_name in self.list_dir(self.path_to_schema()):
            yield file_name

    # delete
    def delete(self, where, _name="name"):
        if len(where) == 1 and _name in where:
            os.remove(self.path_to_data(where[_name]))
            return True
