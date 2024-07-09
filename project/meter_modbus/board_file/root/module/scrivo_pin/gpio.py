
from machine import Pin, Signal
from scrivo.dev import DataClassArg

from scrivo import logging
log = logging.getLogger("PIN")


class Config(DataClassArg):
    name = "Home"
    pin = 0
    inverted = None
    mode = None
    pcb_name = ""
    pull = None
    value = None
    pref = False
    drive = None
    alt = None


class PinInit:

    def __init__(self, pin_name, pin_cfg, value=None):

        self.name = pin_name
        self.pin = None
        pin_cfg = Config(**pin_cfg)
        _kwargs = {}

        if pin_cfg.mode:
            _kwargs["mode"] = getattr(Pin, pin_cfg.mode)
        if pin_cfg.pull:
            _kwargs["pull"] = getattr(Pin, pin_cfg.pull)
        if pin_cfg.value is not None:
            _kwargs["value"] = pin_cfg.value
        if pin_cfg.drive:
            _kwargs["drive"] = getattr(Pin, pin_cfg.drive)
        if pin_cfg.alt:
            _kwargs["alt"] = getattr(Pin, pin_cfg.alt)

        pin_id = pin_cfg.pin
        if pin_cfg.pref:
            pin_id = "{}{}".format(pin_cfg.pref, pin_id)

        log.info(f"id: {pin_id}, {_kwargs}")

        if value is not None:
            _kwargs["value"] = value

        if pin_cfg.inverted is not None:
            log.info(f"Signal - invert: {pin_cfg.inverted}")
            _kwargs["invert"] = pin_cfg.inverted
            self.pin = Signal(pin_id, **_kwargs)  # (pin_arguments..., *, invert=False
        else:
            log.info("Normal:")
            self.pin = Pin(pin_id, **_kwargs)

        log.info(f"PIN: Activate: {pin_name} - {self.pin}")

    def __repr__(self):
        return f"{self.name} - {self.pin}"

    def __str__(self):
        return f"{self.name} - {self.pin}"



