
import asyncio
from scrivo.platform import launch

from scrivo.module import Module

from scrivo import logging
log = logging.getLogger("tele")
# log.setLevel(logging.DEBUG)

import gc
import micropython
import socket

'''
https://github.com/home-assistant/core/blob/dev/homeassistant/components/mqtt/abbreviations.py
'cu': 'configuration_url',
'cns': 'connections',  list | map (optional)
'ids': 'identifiers',  list | string
'name': 'name',
'mf': 'manufacturer',
'mdl': 'model',
'hw': 'hw_version',
'sw': 'sw_version',
'sa': 'suggested_area',
'''

REGISTRY_TELE = []

class Telemetry(Module):
    def reg_config(self):
        pass

    @staticmethod
    def add_config(cfg_type, name, **kwargs):
        REGISTRY_TELE.append(Config(cfg_type, name, **kwargs))

    def notify(self):
        pass


class Runner(Module):

    _prefix = "homeassistant"
    _alive = False
    _mf = "Viktor Vorobjov"

    def activate(self, props):

        #for config in props.configs:
        log.info(f"Add Config params to module: {props.configs}")

        self.mqtt = self.core.env("mqtt")
        self.dev_name = self.core.board.name

        self.dev_t = self.mqtt.client_topic
        self.event_t = f"{self.dev_t}/event"
        self.avty_t = f"{self.dev_t}/status"
        self.cmd_t = f"{self.dev_t}/cmd"

        self.dev = {
            "ids": self.core.board.board_id,
            "name": self.dev_name,
            "sw": '1.0',
            "mdl": f"{self.dev_name}",
            "mf": self._mf,
        }

        for config in props.configs:
            #parse dict with key value
            for key, value in config.items():
                try:
                    path_runner = f"scrivo_{key}._telemetry"
                    mod_runnner = __import__(path_runner, None, None, ["_telemetry"], 0).Runner
                    _telemetry = mod_runnner(name=f"telemetry_{key}", env=key)
                    _telemetry.activate(props=self)
                    _env = self.core.env(key)
                    _env.telemetry = _telemetry
                except Exception as e:
                    log.error(f"Telemetry activate: {e}")
        launch(self.telemetry_alive)

    async def telemetry_alive(self):
        while True:
            await asyncio.sleep(5)
            if not self._alive and self.mqtt.alive:
                log.info(f"Telemetry alive start")
                self._alive = True

                for env in self.core.env().values():
                    if hasattr(env, "telemetry"):
                        try:
                            env.telemetry.reg_config()
                        except Exception as e:
                            log.error(f"Telemetry reg_config: {e}")
                    await asyncio.sleep(0.01)

                # Public all telemetry config
                while REGISTRY_TELE:
                    # log.info(f"{REGISTRY_TELE}")
                    await self._telemetry_config(REGISTRY_TELE.pop())
                    await asyncio.sleep(0.01)


                for env in self.core.env().values():
                    if hasattr(env, "telemetry"):
                        try:
                            env.telemetry.notify()
                        except Exception as e:
                            log.error(f"Telemetry notify: {e}")
                    await asyncio.sleep(0.01)

                log.info(f"Telemetry alive done")

            if not self.mqtt.alive:
                self._alive = False
                log.debug(f"Telemetry: {self._alive}")







    # @staticmethod
    # def add_config(cfg_type, name, **kwargs):
    #     REGISTRY_TELE.append(Config(cfg_type, name, **kwargs))

        # # iter all env in core
        # for env in self.core.env():
        #     log.info(f"Env: {env}")

            # try:
            #     path_runner = f"scrivo_{env}._telemetry"
            #     mod_runnner = __import__(path_runner, None, None, ["_telemetry"], 0).Telemetry
            #     mod_runnner.activate(props=config)
            # except Exception as e:
            #     log.error(f"Telemetry activate: {e}")

        # self.mqtt = self.core.env("mqtt")
        # self.dev_name = self.core.board.name
        #
        # self.dev_t = self.mqtt.client_topic
        # self.event_t = f"{self.dev_t}/event"
        # self.avty_t = f"{self.dev_t}/status"
        # self.cmd_t = f"{self.dev_t}/cmd"
        #
        # self.dev = {
        #     "ids": self.core.board.board_id,
        #     "name": self.dev_name,
        #     "sw": '1.0',
        #     "mdl": f"{self.dev_name}",
        #     "mf": 'Viktor Vorobjov',
        # }
        #
        # # self.core.action_list.append([self._action, 5, "sec", "Telemetry"])
        # self.core.cron("Telemetry", self._action, 5, "sec")
        # # launch(self._telemetry)
        # self.mbus.sub_h("mqtt/#", self.name, "mqtt_act")

    # async def mqtt_act(self, msg):
    #     if msg.payload == "connect":
    #         self._alive = True
    #         for env in self.core.env().values():
    #             env.notify()
    #     elif msg.payload == "disconnect":
    #         self._alive = False



    async def _telemetry_config(self, cfg):
        uniq_id = f"{self.dev_name}_{cfg.name.lower().replace(' ', '_')}"
        _name = " ".join(word[0].upper() + word[1:] for word in cfg.name.split("_"))
        _config = {
            "name": f"{self.dev_name} {_name}",
            # "ic": "mdi:new-box",
            "avty_t": self.avty_t,
            "uniq_id": uniq_id,
            "dev": self.dev
        }
        if hasattr(cfg, "ent_cat"):
            _config["ent_cat"] = cfg.ent_cat

        if hasattr(cfg, "state"):
            _config["stat_t"] = f"{self.event_t}/{cfg.state}"

        if hasattr(cfg, "cmd"):
            _config["cmd_t"] = f"{self.cmd_t}/{cfg.cmd}"

        if hasattr(cfg, "unit_of_meas"):
            _config["unit_of_meas"] = cfg.unit_of_meas

        if hasattr(cfg, "ic"):
            _config["ic"] = cfg.ic

        if hasattr(cfg, "val_tpl"):

            val_tpl = cfg.val_tpl
            if val_tpl.startswith("!"):
                val_tpl = val_tpl[1:]
                _config["val_tpl"] = f"{{{{ {val_tpl} }}}}"
            else:
                _config["val_tpl"] = f"{{{{ value_json.{val_tpl} }}}}"

        if hasattr(cfg, "stat_cla"):
            _config["stat_cla"] = cfg.stat_cla

        if hasattr(cfg, "dev_cla"):
            _config["dev_cla"] = cfg.dev_cla

        #check in cfg attribute start from "ha_" remove "ha_"  and add to _config
        for attr in dir(cfg):
            if attr.startswith("ha_"):
                _config[attr[3:]] = getattr(cfg, attr)

        _config["force_update"] = True
        _topic = f"{self._prefix}/{cfg.cfg_type}/{self.dev_name}/{uniq_id}/config"
        log.info(f"Telemetry: {_topic}")

        # mqtt = self.core.env("mqtt")

        # gc.collect()
        # log.info(micropython.mem_info())
        # _s = socket.socket()
        # _s.close()
        await self.mqtt.apub_msg(_topic, _config, direct=True, retain=True)
        # await asyncio.sleep(0.01)

        # gc.collect()
        # log.info(micropython.mem_info())
        # _s = socket.socket()
        # _s.close()

        #self.mqtt.pub_msg(_topic, _config, direct=True, retain=True)



        # self.mbus.pub_h(f"{self._prefix}/{cfg.cfg_type}/{self.dev_name}/{uniq_id}/config", _config,
        #                 direct=True, retain=True)

    # async def _action(self):
    #     # Telemetry MQTT discovery configure
    #     if self._alive:
    #         while REGISTRY_TELE:
    #             await self._telemetry_config(REGISTRY_TELE.pop())
    #             await asyncio.sleep(0.1)


class Config:

    def __init__(self, cfg_type, name, **kwargs):
        self.cfg_type = cfg_type
        self.name = name

        for key, value in kwargs.items():
            setattr(self, key, value)

    # define how print class
    def __repr__(self):
        return f"Config: {self.cfg_type} - {self.name}"

