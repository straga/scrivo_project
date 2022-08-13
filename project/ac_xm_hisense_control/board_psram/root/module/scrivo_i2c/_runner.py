
from scrivo.loader.loader import Load
from scrivo.thread.thread import run_in_executer
from .bus import I2Cbus

from scrivo import logging
log = logging.getLogger("I2C")


class Runner(Load):

    async def _activate(self):
        self.bus = {}
        await self.activate_bus()

    async def activate_bus(self):
        configs = await self.uconf.call("scan_name", "i2c_cfg")
        for config in configs:
            #Get is2 bus object
            bus_obj = await self.uconf.call("select_one", "i2c_cfg", config, model=True)
            #Get pin_env from env
            pin_env = self.core.env["pin"]
            bus_env = False
            if bus_obj and pin_env:
                #Make hardware pin
                scl = await pin_env.get_pin(pin_name=bus_obj.scl)
                sda = await pin_env.get_pin(pin_name=bus_obj.sda)
                if scl and sda:
                    #Make i2c bus
                    # bus_env = await run_in_executer(I2Cbus, scl=scl, sda=sda, bus_id=bus_obj.id, freq=bus_obj.freq)
                    bus_env = I2Cbus(scl=scl, sda=sda, bus_id=bus_obj.id, freq=bus_obj.freq)
                    self.bus[bus_obj.name] = bus_env
            log.info("BUS: {} - activate: {}".format(bus_obj.name, bus_obj.id))
            if bus_env:
                log.info("i2c BUS: {}, scan: {}".format(bus_obj.name, bus_env.bus.scan()))

        # self.mbus.pub_h("i2c/sensor", "activate")

    def get_bus(self, name):
        result = False
        if name in self.bus:
            result = self.bus[name]
        return result
