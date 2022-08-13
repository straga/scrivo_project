import machine
from scrivo.dev import asyncio
from scrivo.loader.loader import Load
from scrivo.dev import launch

from scrivo import logging
log = logging.getLogger("BINARY")
# log.setLevel(logging.DEBUG)

import utime as time

class BinaryPin:

    def __init__(self, pin, name, on=None, delay=100):
        self.name = name
        self.pin = pin
        self.lock = False
        self.on = on
        self.on_data = None
        self.delay = delay/1000
        self.init_value = pin.value()
        self.value = self.init_value
        self.tick_call = 0
        self.tick_value = 0
        self.period = 0


class Runner(Load):
    bin_list = {}

    async def _activate(self):
        # add for automaticly or not from sensor confif. Now work over control
        pass

    async def get_binary(self, bin_name):

        # check if already configurated
        binary_sensor = False
        if bin_name in self.bin_list:
            binary_sensor = self.bin_list[bin_name]
        else:

            binary_obj = await self.uconf.call("select_one", "binary_sensor_cfg", bin_name, model=True)
            pin_env = self.core.env["pin"]

            try:
                hw_pin = await pin_env.get_pin(pin_name=binary_obj.pin)
                log.info(f"Binary Sensor Pin ID: {hw_pin}")
                log.info(f"Binary Data: {binary_obj.__dict__}")
                id_binary = f"{hw_pin}"
                binary_sensor = BinaryPin(pin=hw_pin, name=binary_obj.name, on=binary_obj.on)
                binary_sensor.on_data = binary_obj.on_data
                log.info(f"Binary Sensor On: {binary_obj.on_data}")
                AsyncPin(binary_sensor=binary_sensor, callback=self.callback,
                         trigger=binary_obj.trigger,
                         wake=binary_obj.wake,
                         priority=binary_obj.priority,
                         hard=binary_obj.hard)

                log.info( f"Binary Sensor Init: name={binary_sensor.name}, pin={binary_sensor.pin}, on={binary_sensor.on}")
                self.bin_list[id_binary] = binary_sensor

            except Exception as e:
                log.error(f"Name: {bin_name}, Error:name {e}")
                pass

        return binary_sensor

    async def callback(self, binary_sensor):
        val = binary_sensor.value
        if binary_sensor.on_data:
            val = binary_sensor.on_data[val]
        log.debug(f"Name: {binary_sensor.name} - value:{val}")
        self.mbus.pub_h(f"binary_sensor/{binary_sensor.name}", val)
        await asyncio.sleep(0)


class AsyncPin:
    def __init__(self, binary_sensor, callback=None, trigger=None, priority=None, wake=None, hard=None):
        self.binary_sensor = binary_sensor
        self.flag = asyncio.ThreadSafeFlag()
        self.callback = callback
        launch(self.wait_callback)

        _kwargs = {
            "handler": lambda lam_pin: self.flag.set()
        }

        if trigger:
            if len(trigger) > 1:
                _kwargs["trigger"] = getattr(machine.Pin, trigger[0]) | getattr(machine.Pin, trigger[1])
            else:
                _kwargs["trigger"] = getattr(machine.Pin, trigger[0])
        if priority:
            _kwargs["priority"] = priority
        if wake:
            _kwargs["wake"] = getattr(machine, wake)
        if hard is not None:
            _kwargs["hard"] = hard

        log.info(f"IRQ Init: {_kwargs}")
        self.binary_sensor.pin.irq(**_kwargs)

    async def wait_edge(self):
        await self.flag.wait()

    async def wait_callback(self):

        while True:
            await self.wait_edge()
            await asyncio.sleep(self.binary_sensor.delay)
            self.binary_sensor.tick_value = time.ticks_ms() - self.binary_sensor.tick_call
            self.binary_sensor.tick_call = time.ticks_ms()
            self.binary_sensor.value = self.binary_sensor.pin.value()
            log.debug(f"Name: {self.binary_sensor.name} - value:{self.binary_sensor.value} - period:{self.binary_sensor.tick_value}")
            if self.callback:
                await self.callback(self.binary_sensor)











