import struct
from scrivo.dev import hexh

from scrivo import logging
log = logging.getLogger("MODBUS")

STORE = {}


class Registry:

    def __init__(self, name):
        self.name = name
        self.sensors = {}
        self.requests = []
        STORE[self.name] = self

    def register_sensor(self, sensor):
        self.sensors[f"{sensor.name}"] = sensor

    def register_botton(self, button):
        pass

    def get_sensor(self, name):
        try:
            return self.sensors[f"{name}"]
        except KeyError:
            log.error(f"Sensor {name} not found in registry {self.name}")
            return None

    def register_modbus(self, modbus):
        self.requests.append(modbus)

    def __call__(self, name):
        return self.get_sensor(name)


class ModbusRequestFactory:

    def __init__(self, addr, func, data_type, registry):
        self.addr = addr
        self.func = func
        self.data_type = data_type
        self.registry = registry


    def __call__(self, modbus_reg, name, **kwarg):
        if self.data_type.mode == "sensor":
            data_instance = self.data_type(name, **kwarg)
            data_instance.stat_t = f"{data_instance.mode}/{self.registry}_{data_instance.name.lower().replace(' ', '_')}/state"
            data_instance.register_sensor(self.registry)

            modbus_instance = ModbusRequest(self.addr, self.func, modbus_reg, name, data_instance)
            STORE[self.registry].register_modbus(modbus_instance)

        elif self.data_type.mode == "button":
            data_instance = self.data_type(name, **kwarg)
            data_instance.cmd_t = f"{data_instance.mode}/{self.registry}_{data_instance.name.lower().replace(' ', '_')}/set"
            modbus_instance = ModbusRequest(self.addr, self.func, modbus_reg, name, data_instance)
            data_instance.request = modbus_instance
            data_instance.register_sensor(self.registry)


            # modbus_instance = ModbusRequest(self.addr, self.func, modbus_reg, name)
            # self.registry.register_modbus(modbus_instance)


class BaseData:
    name = None
    alive = 0
    mode = None
    _value = None
    registry = None

    def result(self):
        if self.alive < 0 and self._value is not None:
            self._value = None
        self.alive -= 1
        return self._value

    def register_sensor(self, registry):
        self.registry = STORE[registry]
        self.registry.sensors[f"{self.name}"] = self

    def __repr__(self):
        return self.__str__()


class VirtualSensor(BaseData):
    alive = 0
    mode = "sensor"

    def __init__(self, name, unit, keys, factor, registry):
        self.name = name
        self.unit = unit
        self.keys = keys
        self.factor = factor
        self.stat_t = f"{self.mode}/{registry}_{self.name.lower().replace(' ', '_')}/state"
        self.register_sensor(registry)
        self.registry = STORE[registry]

    def __str__(self):
        return f"{self.name} {self.unit} : <{self._value}>"

    @property
    def value(self):
        self._value = None
        return self.result()


class SensorMatch(VirtualSensor):

    @property
    def value(self):
        try:
            _value = 0
            for key, factor in zip(self.keys, self.factor):
                s = self.registry.get_sensor(key)
                if s.value is None:
                    self._value = None
                    break
                _value += s.value * factor
            # Done
            self._value = _value
            self.alive = 10
        except Exception as e:
            log.error(f"{self} : {e}")
            self._value = None

        return self.result()

    # @property
    # def value(self):
    #     try:
    #         if isinstance(self.factor, (tuple)):
    #             _value = 0
    #             for key, factor in zip(self.keys, self.factor):
    #                 s = self.registry.get_sensor(key)
    #                 if s.value is None:
    #                     self._value = None
    #                     break
    #                 _value += s.value * factor
    #             self._value = _value
    #             self.alive = 10
    #             # self._value = sum([self.registry(key).value * factor for key, factor in zip(self.keys, self.factor)])
    #
    #         elif callable(self.factor):
    #             slist = []
    #             for key in self.keys:
    #                 s = self.registry.get_sensor(key)
    #                 if s.value is not None:
    #                     slist.append(s.value)
    #
    #             if len(slist) == len(self.keys):
    #                 self._value = self.factor(*slist)
    #                 self.alive = 10
    #     except Exception as e:
    #         log.error(f"{self} : {e}")
    #         self._value = None
    #     return self.result()


class DataSensor(BaseData):
    mode = "sensor"
    _type = None
    _fmt = None
    _size = 2  # default size, 2 byte per register
    recv_bytes = None


    def __init__(self, name, unit=None, factor=1, offset=0, roundf=2):
        self.name = name
        self.unit = unit
        self.factor = factor
        self.offset = offset
        self.roundf = roundf


    @property
    def modbus_reg_qty(self):
        return self._size // 2  # 2 bytes per register

    def deserialize(self):
        # cut data size
        _value = None
        if self.recv_bytes is not None:
            self.value_bytes = self.recv_bytes[3:-2]  # remove header and crc

            if len(self.value_bytes) == self._size: # check if data is valid size
                # unpack to value
                if self._fmt:
                    _value = struct.unpack(self._fmt, self.value_bytes)[0]
                    _value = _value * self.factor + self.offset
                    _value = round(_value, self.roundf)

        self._value = _value

        # debug
        log.debug(f"{self}")

    # def serialize(self):
    #     _value = (self._value - self.offset) / self.factor
    #     _recv_bytes = struct.pack(self._fmt, _value)
    #     self.send_bytes = _recv_bytes

    def __str__(self):
        return f"{self._type}: {hexh(self.recv_bytes)} <{self._value}>"

    @property
    def value(self):
        self.deserialize()
        return self.result()

class DataButton(BaseData):
    mode = "button"
    _type = None
    _fmt = None
    _size = 2  # default size, 2 byte per register
    recv_bytes = None
    send_bytes = None
    request = None
    cmd_t = None

    def __init__(self, name):
        self.name = name

    @property
    def modbus_reg_qty(self):
        return self._size // 2  # 2 bytes per register


    def serialize(self):
        self.send_bytes = struct.pack(self._fmt, self._value)

    def __str__(self):
        return f"{self._type}: {hexh(self.send_bytes)} <{self._value}>"

    def cmd(self, value):
        self._value = value
        self.serialize()
        return self.request

    @property
    def value(self):
        return self.recv_bytes



class ModbusRequest:
    offset = None
    data = None

    def __init__(self, addr, func, reg, name, data):
        self.addr = addr
        self.func = func
        self.reg = reg
        self.name = name
        self.data = data

    def __call__(self, data, alive):
        self.data.recv_bytes = data
        self.data.alive = alive

    def __str__(self):
        return f"addr: {self.addr} func: {self.func} reg: {self.reg} - {self.name} : {self.data}"

    def __repr__(self):
        return self.__str__()

