# Copyright (c) Viktor Vorobjov


from scrivo.core import Core
from scrivo.store import JsonStore

from scrivo import logging
log = logging.getLogger("SWITCH")
#log.setLevel(logging.DEBUG)


class SwitchInit:

    def __init__(self, config):
        self.core = Core.core()
        self.id = config.id
        self.pin_id = config.pin
        self.name = config.name
        self.restore = config.restore

        self._state = ["ON", "OFF"]

        self.pin = None
        self.stat_t = None

        self.cb = None
        self.state = None
        self.store = None

        for attr, value in config.__dict__.items():

            if not attr.startswith('_') and not hasattr(self, attr):
                log.info(f"New atribute: {attr} - {value}")
                setattr(self, attr, value)

        self.init_pin()

    def _restore(self):
        if self.restore is not None:
            if self.restore == "ON":
                return 1
            elif self.restore == "OFF":
                return 0
            elif self.restore == "STATE":
                self.store = JsonStore.get_instance(f"{self.name}.json", delay=5)
                return self.store_state()
        return None

    def init_pin(self):
        pin_env = self.core.env("pin")
        _state = self._restore()
        pin_obj = pin_env.get_pin(pin_id=self.pin_id, value=_state)
        if pin_obj:
            self.pin = pin_obj.pin
            self.stat_t = f"switch/{self.id}/state"
            if self.restore:
                self.change_state(_state)

    # def for call object , retrun state
    def __call__(self, val=None):
        if val is None:
            state_int = self.get_state()
            return self._state[state_int]
        elif isinstance(val, int):
            if val == -1:
                val = None
            return self.change_state(val)
        elif isinstance(val, str):
            val = val.upper()
            if val in self._state:
                val = self._state.index(val)
            return self.change_state(val)

    def get_state(self):
        self.state = self.pin.value()
        return self.state

    def call_cb(self):
        if self.cb:
            self.cb(self)

    def change_state(self, _set=None):
        if _set == -1 and self.state is not None:
            self.pin.value(self.state)
        elif _set is not None and isinstance(_set, int):
            self.pin.value(_set)
        elif _set is None:
            self.pin.value(1 - self.pin.value())
        else:
            return

        self.state = self.pin.value()
        self.call_cb()
        if self.store:
            self.store_state(self.state)
        return self.state

    def store_state(self, val=None):
        if val is None:
            val = self.store.get("state", 0)
        else:
            val = self.store.set("state", val)
        return val

    def __repr__(self):
        return f"{self.name} - {self.pin} "

    def __str__(self):
        return f"Switch: {self.name} - {self.pin}"
