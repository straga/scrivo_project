
from scrivo.dev import hexh
from .crc16_modbus import calc_crc16, check_crc16

import struct

from scrivo import logging
log = logging.getLogger("MODBUS")
# log.setLevel(logging.INFO)

reg_code = {
    0x01: 0,
    0x02: 10001,
    0x03: 40001,
    0x04: 30001,
}

'''
1-9999	    0000 до 270E	Чтение-запись	Discrete Output Coils	        DO
10001-19999	0000 до 270E	Чтение	        Discrete Input Contacts	        DI
30001-39999	0000 до 270E	Чтение	        Analog Input Registers	        AI
40001-49999	0000 до 270E	Чтение-запись	Analog Output Holding Registers	AO

01 (0x01)	Чтение DO	            Read Coil Status	        Дискретное	Чтение
02 (0x02)	Чтение DI	            Read Input Status	        Дискретное	Чтение
03 (0x03)	Чтение AO	            Read Holding Registers	    16 битное	Чтение
04 (0x04)	Чтение AI               Read Input Registers	    16 битное	Чтение
05 (0x05)	Запись одного DO	    Force Single Coil	        Дискретное	Запись
06 (0x06)	Запись одного AO	    Preset Single Register	    16 битное	Запись
15 (0x0F)	Запись нескольких DO	Force Multiple Coils	    Дискретное	Запись
16 (0x10)	Запись нескольких AO	Preset Multiple Registers	16 битное	Запись

первый регистр AO Holding Register, имеет номер 40001, но его адрес равен 0000

Modbus Coils	Bits, binary values, flags	    00001
Digital Inputs	Binary inputs	                10001
Analog Inputs	Binary inputs	                30001
Modbus Registers	Analog values, variables	40001

'''

ALIVE = 10


class Modbus:

    @staticmethod
    def make_request(request):
        _send_bytes = None
        if hasattr(request.data, "send_bytes"):
            _send_bytes = request.data.send_bytes
            if request.func in (0x05, 0x06, 0x0F, 0x10) and _send_bytes is None:
                return None

        _reg_qty = request.data.modbus_reg_qty
        request_pdu = struct.pack('>BBHH', request.addr, request.func, request.reg, _reg_qty)
        # DEBUG
        log.debug(f"  Request : {request}")
        log.debug(f"  Pdu RAW : {hexh(request_pdu)}")

        modbus_pdu = bytearray()
        modbus_pdu.extend(request_pdu)

        # if need send data
        if _send_bytes is not None:
            # Get data from request
            modbus_pdu.append(len(_send_bytes))
            modbus_pdu.extend(_send_bytes)
            # Clear data from request
            request.data_bytes = None

        modbus_pdu.extend(calc_crc16(modbus_pdu))

        # DEBUG
        log.debug(f"  Pdu UART : {hexh(modbus_pdu)}")

        return modbus_pdu

    # modbus_pdu = bytearray()
    # modbus_pdu.append(unit_addr)  # unit_addr
    # modbus_pdu.extend(struct.pack('B', reg_func))  # reg_func
    # modbus_pdu.extend(value_byte)  # value_byte
    # modbus_pdu.extend(calc_crc16(modbus_pdu))  # crc

    @staticmethod
    def parse_response(request, data):
        log.debug(f"<<recv: {hexh(data)} {len(data)}")
        if len(data) > 3 and data[0] != request.addr:
            return None

        crc, _data = check_crc16(data)
        if crc:
            unit_addr, reg_func, byte_qty = struct.unpack_from('BBB', _data, 0)
            request_offset = None
            if reg_func in reg_code:
                request_offset = request.offset
            # DEBUG
            log.debug(
                f"unit_addr: {unit_addr}, reg_offset: {request_offset}, byte_qty: {byte_qty}, data: {hexh(_data)}")

            request(data, ALIVE)
            request.offset = request_offset

            return True

    # @staticmethod
    # def get_data(request):
    #     if hasattr(request, "raw"):
    #         return request.raw[3:-2]
