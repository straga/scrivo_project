# Copyright (c) Viktor Vorobjov

from scrivo_telemetry._runner import Telemetry
from scrivo import logging
log = logging.getLogger("tele")

class Runner(Telemetry):

    def activate(self, props):
        self.tele = self.core.env("switch")
        log.info("TELEMETRY from SWITCH")

        #self.mbus.sub_h("cmd/button/board/#", self.name, "telemetry.button_act")


    def notify(self):
        self.tele.notify()

    def reg_config(self):

        for sw in self.tele._switchs.values():
            log.info(f"SWITCH: {sw}")
            ic = "mdi:toggle-switch"
            if hasattr(sw, "ic"):
                ic = sw.ic

            if sw.mode == "switch" or sw.mode is None:
                self.add_config("switch", sw.name, state=sw.stat_t, cmd=f"switch/{sw.id}/set", ic=ic)
            elif sw.mode == "button":
                self.add_config("button", sw.name, cmd=f"switch/{sw.id}/set", ic=ic)
                self.add_config("sensor", sw.name, state=sw.stat_t, ic=ic)


    #                         sw.ic = "mdi:toggle-switch"
    #
    #                     if sw.mode == "switch" or sw.mode is None:
    #                         self.add_config("switch", sw.name_human, state=sw.stat_t, cmd=f"switch/{att_arg}/set", ic=sw.ic)
    #                     elif sw.mode == "button":
    #                         self.add_config("button", sw.name_human, cmd=f"switch/{att_arg}/set", ic=sw.ic)
    #                         self.add_config("sensor", sw.name_human, state=sw.stat_t, ic=sw.ic)


# import asyncio
# from scrivo.core import Core
# from scrivo.module import Module
# from scrivo.dev import DataClassArg
# from scrivo.store import JsonStore
#
# from scrivo import logging
# log = logging.getLogger("SWITCH")
# #log.setLevel(logging.DEBUG)
#
# # For DEBUG put the following line in the main.py file
# # log = logging.getLogger("SWITCH")
# # log.setLevel(logging.DEBUG)
#
#
# # class SwitchCfg:
# #     sw_led = {
# #         "pin": "pin_led",
# #         "restore": "ON"
# #     }
# class Config(DataClassArg):
#     name = "Home"
#     pin = ""
#     restore = "ON"
#
# class SwitchInit:
#
#     def __init__(self, _name, **kwargs):
#         self.core = Core.core()
#         self.name_human = kwargs.get("name", _name)  # if send name use it else use _name
#         self.name = _name
#         self._pin = kwargs.get("pin")
#         self.pin = None
#         self.stat_t = None
#         self.restore = kwargs.get("restore", None)
#         self.mode = kwargs.get("mode", None)
#         self.ic = kwargs.get("ic", None)
#         self.cb = None
#         self.state = None
#         self.store = None
#         self._state = kwargs.get("state", ["OFF", "ON"])
#
#         self.sw = None
#         _state = None
#         # Restore mode
#         if self.restore is not None:
#             if self.restore == "ON":
#                 _state = 1
#             elif self.restore == "OFF":
#                 _state = 0
#             elif self.restore == "STATE":
#                 self.store = JsonStore.get_instance(f"{self.name}.json", delay=5)
#                 _state = self.store_state()
#
#         pin_env = self.core.env("pin")
#         pin_obj = pin_env.get_pin(pin_name=self._pin, value=_state)
#         if pin_obj:
#             self.pin = pin_obj.pin
#             self.stat_t = f"pin/{pin_obj.name}/state"
#             if self.restore:
#                 self.change_state(_state)
#
#     # def for call object , retrun state
#     def __call__(self, val=None):
#         if val is None:
#             state_int = self.get_state()
#             return self._state[state_int]
#         elif isinstance(val, int):
#             if val == -1:
#                 val = None
#             return self.change_state(val)
#         elif isinstance(val, str):
#             val = val.upper()
#             if val in self._state:
#                 val = self._state.index(val)
#             return self.change_state(val)
#
#     def get_state(self):
#         self.state = self.pin.value()
#         return self.state
#
#     def call_cb(self):
#         if self.cb:
#             self.cb(self)
#
#     def change_state(self, _set=None):
#         if _set == -1 and self.state is not None:
#             self.pin.value(self.state)
#         elif _set is not None and isinstance(_set, int):
#             self.pin.value(_set)
#         elif _set is None:
#             self.pin.value(1 - self.pin.value())
#         else:
#             return
#
#         self.state = self.pin.value()
#         self.call_cb()
#         if self.store:
#             self.store_state(self.state)
#         return self.state
#
#
#     def store_state(self, val=None):
#         if val is None:
#             val = self.store.get("state", 0)
#         else:
#             val = self.store.set("state", val)
#         return val
#
#
# class Config:
#     pass
#
#
# class Runner(Module):
#     depend = ["pin"]
#     # sw_list = {}
#     lock = asyncio.Lock()
#
#     async def _activate(self):
#         # self.core.action_list.append([self.telemetry, 10, "sec", "SWITCH"])
#         self.sub_h(topic="cmd/switch/#", func="sub_control")
#         self.get_switch()
#
#     # def telemetry(self):
#     #     for k, v in self.sw_list.items():
#     #         self.mbus.pub_h("switch/{}/state".format(k), self.get_state(v), retain=False)
#
#     def get_switch(self, sw_name=None):
#         sw = None
#         if sw_name is None:
#             for att_arg, att_val in self.cfg.__dict__.items():
#                 if att_arg.startswith("sw") and not isinstance(att_val, SwitchInit):
#                     sw = SwitchInit(att_arg, **att_val)
#                     sw.cb = self.callback
#                     setattr(self.cfg, att_arg, sw)
#
#                     if sw.ic is None:
#                         sw.ic = "mdi:toggle-switch"
#
#                     if sw.mode == "switch" or sw.mode is None:
#                         self.add_config("switch", sw.name_human, state=sw.stat_t, cmd=f"switch/{att_arg}/set", ic=sw.ic)
#                     elif sw.mode == "button":
#                         self.add_config("button", sw.name_human, cmd=f"switch/{att_arg}/set", ic=sw.ic)
#                         self.add_config("sensor", sw.name_human, state=sw.stat_t, ic=sw.ic)
#         else:
#             sw = getattr(self.cfg, sw_name)
#         return sw
#
#     # notify all state from cfg
#     def notify(self):
#         for att_arg, att_val in self.cfg.__dict__.items():
#             if att_arg.startswith("sw") and isinstance(att_val, SwitchInit):
#                 self.callback(att_val)
#
#
#     def callback(self, sw):
#         self.mbus.pub_h(sw.stat_t, self.get_state(sw), retain=True)
#
#     def sub_control(self, msg):
#         log.debug(f"Switch Ctrl: {msg}")
#         if msg.key == "set":
#             payload = msg.payload
#             if isinstance(msg.payload, int):
#                 payload = str(msg.payload)
#             elif isinstance(msg.payload, bytes):
#                 payload = msg.payload.decode('utf-8')
#
#             if payload in ["0", "1", "ON", "OFF", "-1", None, "STATE", "PRESS"]:
#                 topic = msg.topic.split("/")[-1]
#                 self.control(topic, payload)
#
#     @staticmethod
#     def get_state(switch):
#         if switch:
#             val = switch.get_state()
#             if val == 1:
#                 return "ON"
#             elif val == 0:
#                 return "OFF"
#
#     def state(self, sw_name):
#         switch = self.get_switch(sw_name)
#         return self.get_state(switch)
#
#     @staticmethod
#     def state_value(value):
#         # 1 or On   : Turn On
#         # 0 or Off  : Turn OFF
#         # -1        : restore from saved state
#         # None      : just change state
#         if value is None:
#             return None
#         if isinstance(value, int):
#             return value
#         if isinstance(value, str):
#             if value == "ON":
#                 value = "1"
#             elif value == "OFF":
#                 value = "0"
#             elif value == "STATE" or value == "PRESS":
#                 return None
#             try:
#                 value = int(value)
#             except Exception as e:
#                 log.error(f"ERROR: {e}")
#             return value
#
#
#     def control(self, sw_name, val=None):
#         val = self.state_value(val)
#         switch = self.get_switch(sw_name)
#         log.debug(f"Switch:{switch}, val:{val}")
#         if switch:
#             switch.change_state(val)
