# Copyright (c) Viktor Vorobjov

import asyncio
from scrivo.module import Module
from scrivo.platform import launch


class Runner(Module):

    led = None

    def activate(self, props):
        for config in props.configs:
            self.led = self.init_pin(config["pin"], config["value"])
        launch(self.blink)

    def init_pin(self, pin, value):
        pin_env = self.core.env("pin")
        return pin_env.get_pin(pin_id=pin, value=value)

    async def blink(self):
        while True:
            if self.led:
                self.led.pin.on()
                await asyncio.sleep(1)
                self.led.pin.off()
                await asyncio.sleep(1)


