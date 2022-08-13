# Copyright (c) Viktor Vorobjov

import sys
import gc
from scrivo.core import Core
from scrivo.dev import is_file_exists, launch, asyncio

from scrivo import logging
log = logging.getLogger("LOADER")

# For DEBUG put the following line in the main.py file
# log = logging.getLogger("LOADER")
# log.setLevel(logging.DEBUG)


def mod_path(type_mod, name_mod):
    upd_mod = "upd/scrivo_{}/{}.py".format(name_mod, type_mod)
    _mod = "scrivo_{}.{}".format(name_mod, type_mod)
    if is_file_exists(upd_mod):
        _mod = "upd.scrivo_{}.{}".format(name_mod, type_mod)
    return _mod


class Action:
    def __init__(self, env, module):

        self.core = Core.get_core()
        self.mbus = self.core.mbus
        self.uconf = self.core.uconf
        self.env = env
        self.module = module
        self.depend = module.depend
        self.wait_depend = None
        launch(self.start)

    # Humanize sub to topic
    def sub_h(self, topic, func):
        return self.mbus.sub_h(topic=topic, env=self.env, func=func)

    async def start(self):
        log.info("")
        log.info("   {}   ".format(self.module.env))
        # Load Data Need new
        await self.uconf.call("from_file", "{}/_conf/data_{}.json".format(self.core.storage_dir, self.module.env))
        log.info("WAIT: Data <- {}/_conf/data_{}.json".format(self.core.storage_dir, self.module.env))
        #
        await self.uconf.call("from_file", "{}/module/{}/_data.json".format(self.core.storage_dir, self.module.env))
        log.info("WAIT: Data <- {}/module/{}/_data.json".format(self.core.storage_dir, self.module.env))

        # Wait dependence if exist.
        if self.depend:
            self.wait_depend = self.sub_h(topic="module/#", func="reg_with_depends")

        log.info("DEPEND: {} : Wait = {}".format(self.module.env, self.depend))

    def reg_without_depends(self):
        launch(self.reg_module)

    def reg_with_depends(self, msg):
        log.debug("RUN WAIT: Module ({}) - wait {}: <- Loaded: {}".format(self.env, self.depend, msg.payload))
        # Remove dependence after loaded
        if msg.payload in self.depend:
            self.depend.remove(msg.payload)

        # No more dependece: unsubscribe
        if not self.depend and self.wait_depend:
            self.mbus.usub(self.wait_depend)
            launch(self.reg_module)

    def done(self):
        del self.core.env[self.env]
        log.info("DONE: Loaded: {}".format(self.env))

    async def reg_module(self):
        try:
            log.info("RUN NOW: {}".format(self.module.env))
            self.module.status = True
            await self.module._activate()
            self.mbus.pub_h("module", self.module.env)
            log.info("")

        except Exception as e:
            log.error("Runner Activate: {} - : {}".format(self.module.env, e))
            pass
        self.done()



class Load:
    def __init__(self, env, depend):
        self.core = Core.get_core()
        self.mbus = self.core.mbus
        self.uconf = self.core.uconf
        self.env = env
        self.depend = depend
        self.status = False

    # Humanize sub to topic
    def sub_h(self, topic, func):
        return self.mbus.sub_h(topic=topic, env=self.env, func=func)

    async def _activate(self):
        pass


class Loader:

    __slots__ = ('mbus', 'uconf', 'core', '_modules')

    def __init__(self, modules):

        self.core = Core.get_core()
        self.mbus = self.core.mbus
        self.uconf = self.core.uconf
        self._modules = modules

        _schema = '''{
            "data": {
                "_schema": "_schema",
                "name": "_module",
                "sch": [
                    ["name", ["str", ""]],
                    ["active", ["bool", true]],
                    ["status", ["str", ""]]
                ]
            }
        }
        '''
        self.uconf.from_string(_schema)

    # 1. Load/Update module list from config to store
    async def module_list(self):

        # Load from storage what module will be
        await self.uconf.call("from_file", "{}/_conf/_mod.json".format(self.core.storage_dir))

    # 2. Activate modules
    async def module_act(self):

        # Get list of modules from store
        _mod_list = await self.uconf.call("scan_name", "_module")
        log.info("Default Modules: {}".format(self._modules))
        log.info("exModules: {}".format(_mod_list))

        # Select active module
        log.info("-")
        for name_mod in _mod_list:
            _mod = await self.uconf.call("select_one", "_module", name_mod, True)
            a_info = ""
            if _mod and type(_mod) != str and _mod.active:
                a_info = "{} : {}".format(_mod.active, _mod.name)
                self._modules.append(_mod.name)
            log.info("Active: {}".format(a_info))
            await asyncio.sleep(0.01)

        # Delete duplicate
        self._modules = list(dict.fromkeys(self._modules))
        log.info("Modules: {}".format(self._modules))

        # Activate data schema for each module
        log.info("-")
        for name_mod in self._modules:
            log.info("Name:    {}".format(name_mod))
            path_data = mod_path("_data", name_mod)
            log.info("  path: {}, ".format(path_data))

            # SCHEMA
            try:
                mod_schema = __import__(path_data, None, None, ["_data"], 0).schema
                if mod_schema:
                    await self.uconf.call("from_string", mod_schema)
                    log.info("  schema: True {}".format(name_mod))
                del sys.modules[path_data]
            except Exception as e:
                log.error("  schema: {} - {}".format(name_mod, e))
                pass

            # DATA
            try:
                mod_data = __import__(path_data, None, None, ["_data"], 0).data
                if mod_data:
                    await self.uconf.call("from_string", mod_data)
                    log.info("  data:   True {} ".format(name_mod))
                del sys.modules[path_data]
            except Exception as e:
                log.error("  data:  {} - {},".format(name_mod, e))
                pass
            await asyncio.sleep(0.01)
            log.info("--")



        log.info("-")
        depends = []
        for name_mod in self._modules:

            gc.collect()

            log.info("Init: {}".format(name_mod))

            path_data = mod_path("_data", name_mod)
            path_runner = mod_path("_runner", name_mod)

            # path_data = "scrivo_{}._data".format(name_mod)
            # path_runner = "scrivo_{}._runner".format(name_mod)

            log.debug("  path: {}, {}".format(path_data, path_runner))

            step=""
            try:
                # import data and runner
                step = "data"
                mod_data = __import__(path_data, None, None, ["_data"], 0)
                step = "runner"
                mod_runnner = __import__(path_runner, None, None, ["_runner"], 0).Runner
                step = "core"
                self.core.env_set(name_mod, mod_runnner, mod_data.depend)
                if not mod_data.depend:
                    depends.append("_{}".format(name_mod))
                del sys.modules[path_data]
                del sys.modules[path_runner]

            except Exception as e:
                log.error(f"Init: {name_mod} - err: {e} <- {step}")
                pass
            await asyncio.sleep(0.01)

        # Garbage
        gc.collect()

        # Activate module from active list
        log.info("-")

        # reg with depends and wait other modules
        for name in list(self.core.env):
            try:
                self.core.env_set("_{}".format(name), Action, self.core.env.get(name))
            except Exception as e:
                log.error("Action: {} - : {}".format(name, e))
                pass
            await asyncio.sleep(0.01)

        # reg without depends, imedendly
        for name in depends:
            try:
                self.core.env[name].reg_without_depends()
            except Exception as e:
                log.error("Run: {} - : {}".format(name, e))
                pass



