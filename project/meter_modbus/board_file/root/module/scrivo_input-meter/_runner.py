
import asyncio
import struct
from machine import UART
from scrivo.module import Module
from scrivo.platform import launch
from scrivo.dev import hexh

from scrivo import logging
log = logging.getLogger("METER")
#log.setLevel(logging.DEBUG)

from lib_modbus.modbus import Modbus
from .config_meter import STORE, registry_name


class Runner(Module):
    delay_response = 0.1
    debug = False

    def activate(self, props):
        log.info(f"Config: {props}")

        self.registry = STORE[registry_name]

        for config in props.configs:
            log.info(f"Add Config params to module: {config}")

            # UART
            _uart = UART(config["uart_id"],
                           baudrate=config["uart_baud"],
                           tx=config["uart_tx"],
                           rx=config["uart_rx"])
            self.uart_swriter = asyncio.StreamWriter(_uart, {})
            self.uart_sreader = asyncio.StreamReader(_uart)

            # Debug
            if config.get("debug"):
                log.setLevel(logging.DEBUG)
                debug = config["debug"]
                if isinstance(debug, list):
                    self.debug = config["debug"]

        launch(self.slave_process)
        launch(self.shows)


    async def slave_process(self):
        while True:
            # Send all requests
            for request in self.registry.requests:
                await self.modbus_ex(request)

            self.shows()

            await asyncio.sleep(5)

    async def modbus_ex(self, request):
        uart_pdu = Modbus.make_request(request)
        if uart_pdu is not None:
            # send request to unit
            log.info(f" >> uart {'Meter'}: {hexh(uart_pdu)}")
            await self.uart_swriter.awrite(uart_pdu)
            # log.info(f" >> uart {'Meter'}: {hexh(uart_pdu)}")
            await asyncio.sleep(self.delay_response)

            try:
                data = await asyncio.wait_for(self.uart_sreader.read(1024), 1)
            except asyncio.TimeoutError:
                log.error(f"Meter got timeout {request.name})")
                return

            log.info(f" << uart {'Meter'}: {hexh(data)}")

            if data != b"":
                try:
                    Modbus.parse_response(request, data)
                except Exception as e:
                    log.error(f"Error parse response {e}")

    def shows(self):
        for sensor in self.registry.sensors.values():
            log.info(f"    {sensor.name}: {sensor.value}")
