
import asyncio

import gc

from scrivo.platform import launch
from scrivo.module import Module

from scrivo import logging
log = logging.getLogger("tele")
# log.setLevel(logging.DEBUG)

import micropython

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


class Telemetry(Module):
    tele = None

    async def add_config(self, cfg_type, name, **kwargs):
        if self.tele is not None:
            cfg = Config(cfg_type, name, **kwargs)
            await self.tele._telemetry_config(cfg)

    async def notify(self):
        await asyncio.sleep(0.01)

    async def apub(self, topic, payload, **kwargs):
        await self.tele.mqtt.apub_msg(topic, payload, **kwargs)


class Runner(Module):

    _prefix = "homeassistant"
    _alive = False
    _in_progress = False
    _mf = "Viktor Vorobjov"
    debug = False
    maxsize = 2
    _telemetry_update = False


    def activate(self, props):

        log.info(f"Add Config params to module: {props.configs}")

        if props.sub == "runner":
            self._runner(props.configs)

        else:

            self.mbus.sub_h("mqtt/#", self.name, "mqtt_act")
            self.mbus.sub_h("cmd/tele/#", self.name, "tele_update")

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
                        _telemetry.activate(props=value)
                        _telemetry.tele = self
                        _env = self.core.env(key)
                        _env.telemetry = _telemetry

                    except Exception as e:
                        log.error(f"Telemetry activate: {e}")

            if self.mqtt.alive:
                self._alive = True
                launch(self.telemetry_update_button)

    def _runner(self, configs):
        for config in configs:
            if config.get("debug") is not None:
                self.debug = config["debug"]
            elif config.get("maxsize") is not None:
                self.maxsize = config["maxsize"]


    def mqtt_act(self, msg):
        if msg.payload == "connect":
            launch(self.telemetry_update_button)
            self._alive = True

        elif msg.payload == "disconnect":
            self._alive = False

    def tele_update(self, msg):
        pld = msg.payload_utf8
        log.info(f"Tele update: {msg}")
        if msg.key == "update" and pld == "PRESS":
            launch(self._tele_update)

    async def _tele_update(self):

        if not self._in_progress:

            before = self.mqtt.mqtt.queue.maxsize
            self.mqtt.mqtt.queue.maxsize = self.maxsize

            log.info(f"Telemetry update start: {before} -> {self.maxsize}")
            self._in_progress = True

            for env in self.core.env().values():

                if not self._alive:
                    self._in_progress = False
                    log.warning(f"MQTT is not connected")
                    break

                if hasattr(env, "telemetry"):
                    # Publish telemetry configuration
                    try:
                        await env.telemetry.reg_config()
                    except Exception as e:
                        log.error(f"Telemetry reg_config: {e}")

                    await asyncio.sleep(0.01)

                    # Publish telemetry info
                    await self.notify_update()

            self.mqtt.mqtt.queue.maxsize = before
            self._in_progress = False
            log.info(f"Telemetry update done")

    async def telemetry_update_button(self):
        if self._telemetry_update:
            return
        self.telemetry_update = True
        log.info(f"Telemetry alive start")
        cfg = Config("button", "Telemetry update", ent_cat="diagnostic", cmd="tele/update")
        before = self.mqtt.mqtt.queue.maxsize
        self.mqtt.mqtt.queue.maxsize = 1
        await self._telemetry_config(cfg)
        self.mqtt.mqtt.queue.maxsize = before
        await self.notify_update()
        self.telemetry_update = False

    async def notify_update(self):

        for env in self.core.env().values():
            if hasattr(env, "telemetry"):
                # Publish telemetry info
                try:
                    await env.telemetry.notify()
                except Exception as e:
                    log.error(f"notify_update: {env.name} - {e}")

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

        gc.collect()
        if self.mqtt.alive:
            await self.mqtt.apub_msg(_topic, _config, direct=True, retain=True)
            if self.debug:
                log.info(f"{micropython.mem_info()}")


class Config:

    def __init__(self, cfg_type, name, **kwargs):
        self.cfg_type = cfg_type
        self.name = name

        for key, value in kwargs.items():
            setattr(self, key, value)

    # define how print class
    def __repr__(self):
        return f"Config: {self.cfg_type} - {self.name}"

