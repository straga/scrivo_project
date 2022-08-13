
from scrivo_dev_SI7021.si7021 import SI7021
from scrivo.loader.loader import Load

from scrivo.dev import asyncio, launch

from scrivo import logging
log = logging.getLogger("Sensor")


class Runner(Load):

    period = 30

    async def _activate(self):
        launch(self.sensor_monitor)

    async def sensor_monitor(self):
        # await asyncio.sleep(180)

        i2c_env = self.core.env["i2c"]
        log.info("i2c_env: {}".format(i2c_env.bus))
        htu_outside = False

        i2c = i2c_env.get_bus("i2c_0")
        if i2c:
            htu_outside = SI7021(i2c)

        log.info("i2c_0: {}, sensor={}".format(i2c, htu_outside))

        while True:
            # OUTSIDE SI
            try:
                await htu_outside.to_measure()
                if htu_outside.temperature:
                    self.mbus.pub_h("sensor/{}/value".format("ac_temperature"), htu_outside.temperature)
                if htu_outside.humidity:
                    self.mbus.pub_h("sensor/{}/value".format("ac_humidity"), htu_outside.humidity)
            except Exception as e:
                log.error("Err SI{}".format(e))
                pass

            log.info(f"sensor_monitor - {htu_outside.temperature} - {htu_outside.humidity}")
            await asyncio.sleep(self.period)

