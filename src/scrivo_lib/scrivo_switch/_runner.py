# Copyright (c) Viktor Vorobjov

from scrivo.dev import asyncio
from scrivo.loader.loader import Load
from scrivo.tools.tool import launch
from .state import Switch

from scrivo import logging
log = logging.getLogger("SWITCH")

# For DEBUG put the following line in the main.py file
# log = logging.getLogger("SWITCH")
# log.setLevel(logging.DEBUG)

class Runner(Load):
    sw_list = {}

    async def _activate(self):
        self.core.action_list.append([self.telemetry, 10, "sec", "SWITCH"])
        self.sub_h(topic="switch/#", func="sub_control")

    def telemetry(self):
        for k, v in self.sw_list.items():
            self.mbus.pub_h("switch/{}/state".format(k), v.get_state(), retain=False)

    async def get_switch(self, sw_name):
        switch = None
        if sw_name in self.sw_list:
            switch = self.sw_list[sw_name]
        else:
            # Get switch from store
            switch_obj = await self.uconf.call("select_one", "switch_cfg", sw_name, model=True)
            # await asyncio.sleep(0.1)

            # Get pin_env from env
            pin_env = self.core.env["pin"]

            if switch_obj and pin_env:
                # Make hardware pin
                switch_pin = await pin_env.get_pin(pin_name=switch_obj.pin, value=self.state_value(switch_obj.state))
                if switch_pin:
                    # Make switch
                    switch = Switch(pin=switch_pin, name=switch_obj.name)
                    switch.cb = self.cb
                    self.mbus.pub_h("switch/{}/init".format(switch_obj.name), [switch_obj.pin])
                    self.sw_list[switch_obj.name] = switch

                    # Restore mode
                    if switch_obj.restore is not None:
                        if switch_obj.restore == "ON":
                            switch.change_state(1)
                        elif switch_obj.restore == "OFF":
                            switch.change_state(0)
                        elif switch_obj.restore == "STATE":
                            switch.restore = True
                            switch.change_state(switch_obj.state)

        return switch

    async def save_stage(self, switch):
        switch_obj = await self.uconf.call("select_one", "switch_cfg", switch.name, model=True)
        switch_obj.state = switch.state
        await switch_obj.update()

    def cb(self, sw):
        self.mbus.pub_h("switch/{}/state".format(sw.name), sw.get_state(), retain=False)
        if sw.restore:
            launch(self.save_stage, sw)

    async def sub_control(self, msg):
        log.debug(f"sub_control: t: {msg.topic},  k: {msg.key}, p: {msg.payload}")
        if msg.key == "set":
            payload = msg.payload
            if isinstance(msg.payload, int):
                payload = str(msg.payload)
            elif isinstance(msg.payload, bytes):
                payload = msg.payload.decode('utf-8')

            if payload in ["0", "1", "ON", "OFF", "-1", None, "STATE"]:
                topic = msg.topic.split("/")[-1]
                await self.control(topic, payload)

    async def state(self, sw_name):
        result = None
        switch = await self.get_switch(sw_name)
        if switch:
            result = switch.get_state()
        return result

    def state_value(self, value):
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
            elif value == "STATE":
                return None
            try:
                value = int(value)
            except Exception as e:
                log.error(f"ERROR: {e}")
            return value

    async def control(self, sw_name, val=None):
        val = self.state_value(val)
        switch = await self.get_switch(sw_name)
        log.debug(f"Switch:{switch}, val:{val}")
        if switch:
            switch.change_state(val)
