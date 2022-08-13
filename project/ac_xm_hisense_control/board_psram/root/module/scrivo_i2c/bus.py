
try:
    from uasyncio import Lock
except Exception:
    from asyncio import Lock


class I2Cbus:

    def __init__(self, scl, sda, bus_id=-1, freq=400000):

        if bus_id > -1:
            from machine import I2C  # hardware
            self.bus = I2C(bus_id, scl=scl, sda=sda, freq=freq)
        else:
            from machine import SoftI2C  # software
            self.bus = SoftI2C(scl=scl, sda=sda, freq=freq)

        self.lock = Lock()
