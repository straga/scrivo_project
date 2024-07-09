import math
from lib_modbus.factory import ModbusRequestFactory, VirtualSensor, DataSensor, DataButton, Registry, STORE

registry_name = "Meter"
Registry(registry_name)


VOLT = "V"
AMP = "A"
WATT = "W"
KWH = "kWh"
COSF = "CosF"
HZ = "Hz"
VAR = "VAr"
VA = "VA"


class FloatingPoint(DataSensor):
    _type = "float"
    _fmt = ">f"
    _size = 4


# # Sensors
#
float_sensor = ModbusRequestFactory(addr=1, func=0x04, data_type=FloatingPoint, registry=registry_name)

# # Voltage
float_sensor(0x0000, "IN Voltage L1", unit=VOLT, roundf=2)
float_sensor(0x0002, "IN Voltage L2", unit=VOLT, roundf=2)
float_sensor(0x0004, "IN Voltage L3", unit=VOLT, roundf=2)

# # Current
float_sensor(0x0006, "IN Current L1", unit=AMP, roundf=2)
float_sensor(0x0008, "IN Current L2", unit=AMP, roundf=2)
float_sensor(0x000A, "IN Current L3", unit=AMP, roundf=2)

# # Power
float_sensor(0x000C, "IN Power L1", unit=WATT, roundf=2)
float_sensor(0x000E, "IN Power L2", unit=WATT, roundf=2)
float_sensor(0x0010, "IN Power L3", unit=WATT, roundf=2)

# # Reactive
float_sensor(0x0018, "IN Reactive L1", unit=VAR, roundf=2)
float_sensor(0x001A, "IN Reactive L2", unit=VAR, roundf=2)
float_sensor(0x001C, "IN Reactive L3", unit=VAR, roundf=2)

# # Power factor
float_sensor(0x001E, "IN Factor L1", unit=COSF, roundf=2)
float_sensor(0x0020, "IN Factor L2", unit=COSF, roundf=2)
float_sensor(0x0022, "IN Factor L3", unit=COSF, roundf=2)

# # Frequency
float_sensor(0x0046, "IN Frequency", unit=HZ, roundf=2)

# Export
float_sensor(0x0160, "IN Export Active Energy L1", unit=KWH, roundf=2)
float_sensor(0x0162, "IN Export Active Energy L2", unit=KWH, roundf=2)
float_sensor(0x0164, "IN Export Active Energy L3", unit=KWH, roundf=2)

# Import
float_sensor(0x015A, "IN Import Active Energy L1", unit=KWH, roundf=2)
float_sensor(0x015C, "IN Import Active Energy L2", unit=KWH, roundf=2)
float_sensor(0x015E, "IN Import Active Energy L3", unit=KWH, roundf=2)

float_sensor(0x0156, "Total Active Energy", unit=KWH, roundf=2)

# # Reactive power
# float_sensor(0x2006, "G_Reactive power", unit=VAR, roundf=4, factor=1000)

#            // 3P4 3P3 1P2 Unit Description
#   0x0000,  //  +   -   +   V    Phase 1 line to neutral volts
#   0x0002,  //  +   -   -   V    Phase 2 line to neutral volts
#   0x0004,  //  +   -   -   V    Phase 3 line to neutral volts
#   0x0006,  //  +   +   +   A    Phase 1 current
#   0x0008,  //  +   +   -   A    Phase 2 current
#   0x000A,  //  +   +   -   A    Phase 3 current
#   0x000C,  //  +   -   +   W    Phase 1 power
#   0x000E,  //  +   -   +   W    Phase 2 power
#   0x0010,  //  +   -   -   W    Phase 3 power
#   0x0018,  //  +   -   +   VAr  Phase 1 volt amps reactive
#   0x001A,  //  +   -   -   VAr  Phase 2 volt amps reactive
#   0x001C,  //  +   -   -   VAr  Phase 3 volt amps reactive
#   0x001E,  //  +   -   +        Phase 1 power factor
#   0x0020,  //  +   -   -        Phase 2 power factor
#   0x0022,  //  +   -   -        Phase 3 power factor
#   0x0046,  //  +   +   +   Hz   Frequency of supply voltages
#   0x0160,  //  +   +   +   kWh  Phase 1 export active energy
#   0x0162,  //  +   +   +   kWh  Phase 2 export active energy
#   0x0164,  //  +   +   +   kWh  Phase 3 export active energy

# //#ifdef SDM630_IMPORT
#   0x015A,  //  +   +   +   kWh  Phase 1 import active energy
#   0x015C,  //  +   +   +   kWh  Phase 2 import active energy
#   0x015E,  //  +   +   +   kWh  Phase 3 import active energy
# //#endif  // SDM630_IMPORT
#   0x0156   //  +   +   +   kWh  Total active energy



# # Sensors
# float_sensor = ModbusRequestFactory(addr=2, func=0x03, data_type=FloatingPoint, registry=registry_name)
#
# # Voltage
# float_sensor(0x2000, "G_Voltage", unit=VOLT, roundf=2)
#
# # Current
# float_sensor(0x2002, "G_Current", unit=AMP, roundf=2)
#
#
# # Active power
# float_sensor(0x2004, "G_Active power", unit=KWH, roundf=4, factor=1000)
#
#
# # Reactive power
# float_sensor(0x2006, "G_Reactive power", unit=VAR, roundf=4, factor=1000)
#
#
# # Power factor
# float_sensor(0x200A, "G_Power factor", unit=COSF, roundf=2)
#
# # Frequency
# float_sensor(0x200E, "G_Frequency", unit=HZ, roundf=2)
#
# # IMPORT_ACTIVE
# float_sensor(0x4000, "G_Import Total", unit="kW", roundf=2)
#
# # EXPORT_ACTIVE
# float_sensor(0X400A, "G_Export Total", unit="kW", roundf=2)
#
# def apparent_power(active_power, reactive_power):
#     if active_power is None or reactive_power is None:
#         return None
#     return round(math.sqrt(active_power ** 2 + reactive_power ** 2), 2)
#
# # Apparent power
# VirtualSensor("G_Apparent power", unit=VA, keys=["G_Active power", "G_Reactive power"], factor=apparent_power, registry=registry_name)
#
#
# def import_energy(active_power):
#     # if active_power type int
#     if isinstance(active_power, int) and active_power > 0:
#         return active_power
#     else:
#         return 0
#
# def export_energy(active_power):
#     if isinstance(active_power, int) and active_power < 0:
#         return active_power * -1
#     else:
#         return 0
#
# # Import energy
# VirtualSensor("G_Import energy", unit=KWH, keys=["G_Active power"], factor=import_energy, registry=registry_name)
#
# # Export energy
# VirtualSensor("G_Export energy", unit=KWH, keys=["G_Active power"], factor=export_energy, registry=registry_name)
#
#
# # Z Meter
#
# # Sensors
# z_float_sensor = ModbusRequestFactory(addr=1, func=0x03, data_type=FloatingPoint, registry=registry_name)
#
# # Voltage
# z_float_sensor(0x2006, "Z_Voltage L1", unit=VOLT, roundf=2, factor=0.1)
# z_float_sensor(0x2008, "Z_Voltage L2", unit=VOLT, roundf=2, factor=0.1)
# z_float_sensor(0x200A, "Z_Voltage L3", unit=VOLT, roundf=2, factor=0.1)
#
# # Current
# z_float_sensor(0x200C, "Z_Current L1", unit=AMP, roundf=2, factor=0.001)
# z_float_sensor(0x200E, "Z_Current L2", unit=AMP, roundf=2, factor=0.001)
# z_float_sensor(0x2010, "Z_Current L3", unit=AMP, roundf=2, factor=0.001)
#
# # Active power
# z_float_sensor(0x2014, "Z_Active power L1 ", unit=KWH, roundf=4, factor=0.001)
# z_float_sensor(0x2016, "Z_Active power L2 ", unit=KWH, roundf=4, factor=0.001)
# z_float_sensor(0x2018, "Z_Active power L3 ", unit=KWH, roundf=4, factor=0.001)
#
#
# z_float_sensor(0x2012, "Z_Active Total", unit="kW", roundf=2, factor=0.1)
# # IMPORT_ACTIVE
# z_float_sensor(0x401E, "Z_Import Total", unit="kW", roundf=2, factor=1000)

#
# # Total energy
# float_sensor(0x0100, "Total active energy", unit=KWH, roundf=4)
# float_sensor(0x0400, "Total reactive energy", unit=KWH, roundf=4)
#
#
#
# # Apparent power (VA) = √(Active power² (W) + Reactive power² (VARs))
# def apparent_power(active_power, reactive_power):
#     return round(math.sqrt(active_power ** 2 + reactive_power ** 2), 2)
#
#
# # Apparent power
# VirtualSensor("A apparent power", unit=VA, keys=["A active power", "A reactive power"], factor=apparent_power, registry=registry_name)
# VirtualSensor("B apparent power", unit=VA, keys=["B active power", "B reactive power"], factor=apparent_power, registry=registry_name)
# VirtualSensor("C apparent power", unit=VA, keys=["C active power", "C reactive power"], factor=apparent_power, registry=registry_name)

# # TEST
# # Test populate sensor registry for test
# for sensor in modbus_register:
#     sensor_registry[sensor.name.lower().replace(" ", "_")] = sensor.data
#
#
# print(sensor_registry)
#
# for name, sensor in sensor_registry.items():
#     # call update sensor data
#     print(f"{name}: {sensor}")
#     # send data to mqtt
#     print(f"   mqtt: {sensor.value}")
#
# # rundom data  1  to 300 return hex, return 4 bytes
# import random
# def random_data():
#     return struct.pack(">f", random.randint(1, 300))
#
# #Emulate modbus data
# for modbus in modbus_register:
#     # read data from modbus
#     data = random_data()
#     # deserialize data
#     modbus(data)
#
# print(sensor_registry)
#
# for name, sensor in sensor_registry.items():
#     # call update sensor data
#     print(f"{name}: {sensor}")
#     # send data to mqtt
#     print(f"   mqtt: {sensor.value}")
#
# pass
