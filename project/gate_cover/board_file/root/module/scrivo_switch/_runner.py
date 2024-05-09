# Copyright (c) Viktor Vorobjov

import asyncio
from scrivo.core import Core
from scrivo.module import Module
from scrivo.dev import DataClassArg

from scrivo import logging
log = logging.getLogger("SWITCH")
#log.setLevel(logging.DEBUG)


class Config(DataClassArg):
    id = "SW1"
    name = "Home Switch"
    pin = "sw1_output"
    restore = None # ON, OFF, STATE
    mode = "switch" # switch, button


class Runner(Module):

    lock = asyncio.Lock()
    _switchs = {}

    def activate(self, props):
        for config in props.configs:
            if config.get("platform") and config.get("platform") == "binary":
                log.info(f"Add Config params to module: {config}")

                from .switch import SwitchInit
                config = Config.from_dict(config)
                log.info(f" Config: {config}")
                sw = SwitchInit(config)
                sw.cb = self.callback
                self._switchs[config.id] = sw

        self.sub_h(topic="cmd/switch/#", func="sub_control")

    def get_switch(self, sw_id=None):
        sw = self._switchs.get(sw_id, None)
        return sw

    # notify all state from cfg
    def notify(self):
        for sw in self._switchs.values():
            self.callback(sw)


    def callback(self, sw):
        self.mbus.pub_h(sw.stat_t, self.get_state(sw), retain=True)

    def sub_control(self, msg):
        log.debug(f"Switch Ctrl: {msg}")
        if msg.key == "set":
            payload = msg.payload
            if isinstance(msg.payload, int):
                payload = str(msg.payload)
            elif isinstance(msg.payload, bytes):
                payload = msg.payload.decode('utf-8')

            if payload in ["0", "1", "ON", "OFF", "-1", None, "STATE", "PRESS"]:
                topic = msg.topic.split("/")[-1]
                self.control(topic, payload)

    @staticmethod
    def get_state(switch):
        if switch:
            val = switch.get_state()
            if val == 1:
                return "ON"
            elif val == 0:
                return "OFF"

    def state(self, sw_id):
        switch = self.get_switch(sw_id)
        return self.get_state(switch)

    @staticmethod
    def state_value(value):
        # 1 or On   : Turn On
        # 0 or Off  : Turn OFF
        # -1        : restore from saved state
        # None      : just change state
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if value == "ON":
                value = "1"
            elif value == "OFF":
                value = "0"
            elif value == "STATE" or value == "PRESS":
                return None
            try:
                value = int(value)
            except Exception as e:
                log.error(f"ERROR: {e}")
            return value


    def control(self, sw_id, val=None):
        val = self.state_value(val)
        switch = self.get_switch(sw_id)
        log.debug(f"Switch:{switch}, val:{val}")
        if switch:
            switch.change_state(val)
