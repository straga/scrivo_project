# Copyright (c) 2018 Viktor Vorobjov
import uasyncio as asyncio
from ustruct import pack as pk
from micropython import const

from scrivo import logging
log = logging.getLogger("SI7021")

__SI_ADDR = const(0x40)
__SI_RH_READ = const(0xE5)
__SI_TEMP_READ = const(0xE3)
__SI_POST_RH_TEMP_READ = const(0xE0)
__SI_RESET = const(0xFE)
__SI_USER1_READ = const(0xE7)
__SI_USER1_WRITE = const(0xE6)
__SI_CRC8_POLYNOMINAL = const(0x13100)  # CRC8 polynomial for 16bit CRC8 x^8 + x^5 + x^4 + 1
__SI_TRIGGER_TEMP_MEASURE_HOLD = const(0xE3)
__SI_TRIGGER_HUMD_MEASURE_HOLD = const(0xE5)
__SI_TRIGGER_TEMPERATURE_NO_HOLD = const(0xF3)
__SI_TRIGGER_HUMIDITY_NO_HOLD = const(0xF5)


class SI7021:

    def __init__(self, i2c):

        self.i2c = i2c.bus
        self.lock = i2c.lock

        self.present = 0
        self._raw = {}

        self.delays = 100 #ms

        self.temperature = None
        self.humidity = None

    async def sensor_detect(self):
        async with self.lock:
            try:
                reg = self.i2c.readfrom_mem(__SI_ADDR, __SI_USER1_READ, 1)
                self.present = 1
            except Exception as e:
                log.debug("Hum:Err {}".format(e))
                self.present = 0
                pass

        if not self.present:
            log.debug("Sensor Error or not present: {}")
            await self.soft_reset()
        else:
            log.debug("Sensor present / Register Byte: {}, decimal: {}".format(reg[0], reg))

    async def soft_reset(self):
        async with self.lock:
            try:
                self.i2c.writeto(__SI_ADDR, pk('b', __SI_RESET))
            except Exception as e:
                log.debug("Sensor Error or not present: {}".format(e))
                pass


    async def _read_data(self, raw):
        async with self.lock:
            try:
                self._raw[raw] = self.i2c.readfrom(__SI_ADDR, 3)
            except Exception as e:
                log.debug("Read {} Err: {}".format(raw, e))
                pass

    async def to_measure(self):

        async with self.lock:

            # TEMPERATURE_NO_HOLD
            try:
                self.i2c.writeto(__SI_ADDR, pk('b', __SI_TRIGGER_TEMPERATURE_NO_HOLD))
            except Exception as e:
                log.debug("Sensor Temp cmd: {}".format(e))
                self.present = 0
                pass
            await asyncio.sleep_ms(self.delays)  # Wait for device
        await self._read_data("T")

        async with self.lock:
            # HUMIDITY_NO_HOLD
            try:
                self.i2c.writeto(__SI_ADDR, pk('b', __SI_TRIGGER_HUMIDITY_NO_HOLD))
            except Exception as e:
                log.debug("Sensor Humidity cmd Error: {}".format(e))
                self.present = 0
                pass
            await asyncio.sleep_ms(self.delays)  # Wait for device
        await self._read_data("H")

        self.temperature = self._temperature()
        self.humidity = self._humidity()
        self._raw = {}
        if not self.present:
            await self.sensor_detect()

    def _temperature(self):
        try:
            raw_t = self._raw["T"]
        except Exception as e:
            log.debug("Temperature convert Error: {}".format(e))
            pass
            return False

        if not self.crc8check(raw_t):
            log.debug("crc8check raw T: {} - False, ".format(raw_t))
            return False

        raw_temp = (raw_t[0] << 8) + raw_t[1]
        # Clear the status bits
        raw_temp = raw_temp & 0xFFFC
        # Calculate the actual temperature
        actual_temp = -46.85 + (175.72 * raw_temp / 65536)
        actual_temp = round(actual_temp, 2)
        log.debug("Temperature: {} .C".format(actual_temp))
        return actual_temp

    def _humidity(self):
        try:
            raw_h = self._raw["H"]
        except Exception as e:
            log.debug("Humidity convert error: {}".format(e))
            pass
            return None

        if not self.crc8check(raw_h):
            log.debug("crc8check raw T: {} - False, ".format(raw_h))
            return None

        raw_rh = (raw_h[0] << 8) + raw_h[1]
        # Clear the status bits
        raw_rh = raw_rh & 0xFFFC
        # Calculate the actual RH
        actual_rh = -6 + (125.0 * raw_rh / 65536)
        actual_rh = round(actual_rh, 2)
        log.debug("Humidity: {} RH".format(actual_rh))

        return actual_rh


    # POLYNOMIAL = 0x0131 = x^8 + x^5 + x^4 + 1
    # divsor = 0x988000 is polynomial shifted to farthest left of three bytes
    def crc8check(self, value):
        result = False
        remainder = ((value[0] << 8) + value[1]) << 8
        remainder |= value[2]
        divsor = 0x988000

        for i in range(0, 16):
            if remainder & 1 << (23 - i):
                remainder ^= divsor
            divsor = divsor >> 1

        if remainder == 0:
            result = True

        return result



