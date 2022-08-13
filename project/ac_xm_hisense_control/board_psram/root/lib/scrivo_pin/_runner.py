# Copyright (c) 2021 Viktor Vorobjov

from machine import Pin, Signal
from scrivo.loader.loader import Load
from scrivo.dev import asyncio

from scrivo import logging
log = logging.getLogger("PIN")


class Runner(Load):
    pin_list = {}

    async def _activate(self):
        await asyncio.sleep(0.01)

    async def get_pin(self, pin_name, value=None):
        pin = False
        if pin_name in self.pin_list:
            pin = self.pin_list[pin_name]

        else:
            pin_obj = await self.uconf.call("select_one", "pin_cfg", pin_name, model=True)

            if pin_obj:
                _kwargs = {}

                if pin_obj.mode:
                    _kwargs["mode"] = getattr(Pin, pin_obj.mode)
                if pin_obj.pull:
                    _kwargs["pull"] = getattr(Pin, pin_obj.pull)
                if pin_obj.value is not None:
                    _kwargs["value"] = pin_obj.value
                if pin_obj.drive:
                    _kwargs["drive"] = getattr(Pin, pin_obj.drive)
                if pin_obj.alt:
                    _kwargs["alt"] = getattr(Pin, pin_obj.alt)

                pin_id = pin_obj.number
                if pin_obj.pref:
                    pin_id = "{}{}".format(pin_obj.pref, pin_id)

                log.info(f"PIN: id: {pin_id}, {_kwargs}")

                if value is not None:
                    _kwargs["value"] = value

                if pin_obj.inverted is not None:
                    log.info(f"PIN: Signal - invert: {pin_obj.inverted}")
                    _kwargs["invert"] = pin_obj.inverted
                    pin = Signal(pin_id, **_kwargs)  # (pin_arguments..., *, invert=False
                else:
                    log.info("PIN: Normal:")
                    pin = Pin(pin_id, **_kwargs)

                self.pin_list[pin_obj.name] = pin
                log.info(f"PIN: Activate: {pin_obj.name}")
                    # self.mbus.pub_h("pin/{}/init".format(pin_obj.name), [pin_obj.number, pin_obj.mode, pin_obj.pull])
        return pin

