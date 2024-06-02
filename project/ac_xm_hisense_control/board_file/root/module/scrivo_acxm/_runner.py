# Copyright (c) 2024 Viktor Vorobjov
import asyncio
import struct
from machine import UART
from scrivo.module import Module
from scrivo.platform import launch
from scrivo.platform import Queue

import gc

from .responses import _data_template
from .responses import _Data_CMD
from .responses import _Data_101_0, _Data_102_64, _Data_102_0, _Data_7_1, _Data_10_4, _Data_30_0
from .responses import _Setting_101_0, _Setting_102_64, _Setting_102_0, _Setting_7_1, _Setting_10_4, _Setting_30_0

from scrivo import logging
log = logging.getLogger("AC_XM")
#log.setLevel(logging.DEBUG)

HEADER = b'\xF4\xF5' # F4F5 header
FOOTER = b'\xF4\xFB' # F4FB footer


def hexh(data, sep=' '):
    try:
        data = f'{sep}'.join('{:02x}'.format(x) for x in data)
    except Exception as e:
        log.error("HEX: {}".format(e))
    return data


class Runner(Module):
    mode = "normal"  # sniff, cloud, normal
    ac_swriter = None
    ac_sreader = None
    lock = asyncio.Lock()
    ac_init = 0
    ac_ping = 0
    ac_ping_max = 5
    ac_ping_wait = 1  # sec
    ac_process_run = False
    debug = []
    event = asyncio.Event()

    # Configure  store for data from AC
    store_10_4 = [None] * len(_Data_10_4)
    store_7_1 = [None] * len(_Data_7_1)
    store_30_0 = [None] * len(_Data_30_0)

    store_102 = [None] * len(_Data_102_0)
    store_102_64 = [None] * len(_Data_102_64)

    def activate(self, props):
        log.info(f"Config: {props}")

        for config in props.configs:
            log.info(f"Add Config params to module: {config}")

            # UART
            ac_uart = UART(config["uart_id"],
                           baudrate=config["uart_baudrate"],
                           tx=config["uart_tx"],
                           rx=config["uart_rx"])
            self.ac_swriter = asyncio.StreamWriter(ac_uart, {})
            self.ac_sreader = asyncio.StreamReader(ac_uart)

            # Debug
            if config.get("debug"):
                log.setLevel(logging.DEBUG)
                debug = config["debug"]
                if isinstance(debug, list):
                    self.debug = config["debug"]

            # Mode
            if config.get("mode"):
                self.mode = config.get("mode")

            # Start -  or AC init(just for test) or Normal mode
            '''
            Mode:
                sniff - sniffing data from UART - just raw data without detect right packet
                cloud - use for just receive data from AC to AC. When need get data between AC and cloud.
                normal - normal mode
            '''
            if self.mode == "sniff":
                launch(self.sniffer)
            elif self.mode == "cloud":
                launch(self.ac_msg_reader)
            else:
                launch(self.ac_run_init)
                launch(self.ac_msg_reader)



    # sneffing data from UART
    async def sniffer(self):
        while True:
            data = b''
            try:
                data = await asyncio.wait_for(self.ac_sreader.read(1024), 10)
            except asyncio.TimeoutError:
                log.error("got timeout")

            if data != b'':
                log.debug(f"Data: {hexh(data)}")
            await asyncio.sleep(0.1)

    # Read Data from AC over UART with timeout
    async def wait_for_data(self, data_len=1, timeout=10):
        data = None
        try:
            data = await asyncio.wait_for(self.ac_sreader.read(data_len), timeout)
        except asyncio.TimeoutError:
            log.error("got timeout")
        return data

    async def ac_msg_reader(self):

        while True:
            data = None
            # Read 2 bytes and check if it is a packet header
            byte = await self.wait_for_data(2)
            if byte == HEADER:
                # Potential start of packet, check next byte
                data = bytearray(byte)
                while True:
                    byte = await self.wait_for_data(1)
                    data.append(byte[0])
                    if len(data) >= 4 and data[-2:] == FOOTER:
                        # Found packet footer, return packet
                        break

                    await asyncio.sleep(0.01)

            if data is not None:
                if self.mode == "ac_init_test":
                    log.debug(f"Data: {hexh(data)}")
                else:
                    #log.debug(f"Data: {hexh(data)}")
                    self.process_data(data)

            await asyncio.sleep(0.01)



    def process_data(self, data):
        mdata = memoryview(data)

        if "raw" in self.debug:
            log.debug(f" H: {hexh(mdata)}")
        try:
            msg = Message(mdata)
            if self.is_valid_message(msg):
                self.handle_message(msg)
        except Exception as e:
            log.error(f"recv: e: {e}, H:{hexh(mdata)}, ")

        self.event.set()

    def is_valid_message(self, msg):
        msg.step_1_check_len()
        if msg.packet_msg_length > -1:
            msg.step_2_check_crc()
            return msg.crc > -1
        return False

    def handle_message(self, msg):
        msg.unpack_mdata()

        # debug
        if "msg" in self.debug:
            msg.info_msg()

        if msg.paket_type == 0x01:  # if packet type is 0x01, it is a data packet from AC
            if msg.msg_packet_type == 102 or msg.msg_packet_type == 101:
                if msg.packet_msg_length == 8:
                    msg.info_msg()
                # Data from AC
                elif msg.msg_sub_type == 0:
                    self.store_date(msg, _Data_102_0, self.store_102)
                # Power usage from AC
                elif msg.msg_sub_type == 64:
                    self.store_date(msg, _Data_102_64, self.store_102_64)
            # XZ
            elif msg.msg_packet_type == 10 and msg.msg_sub_type == 4:
                self.store_date(msg, _Data_10_4, self.store_10_4)
            # AC sofrware version
            elif msg.msg_packet_type == 7 and msg.msg_sub_type == 1:
                self.store_date(msg, _Data_7_1, self.store_7_1)
            # AC ping data
            elif msg.msg_packet_type == 30 and msg.msg_sub_type == 0:
                self.ac_ping = 1
                self.store_date(msg, _Data_30_0, self.store_30_0)
            else:
                msg.info_msg()

    async def ac_run_init(self):
        while True:
            # AC Init
            if self.ac_init == 0:
                async with self.lock:
                    await self.cmd("10_4", {"init": "act"}, 0.2)
                    await self.cmd("7_1", {"init": "act"}, 0.2)
                    await self.cmd("102_64", {"init": "act"}, 0.2)
                    await self.cmd("30_0", {"init": "act"}, 5)
            else:
                self.ac_ping = self.ac_ping + 1
                async with self.lock:
                    await self.cmd("30_0", {"period": "act"}, 0.2)
                    await self.cmd("102_0", {"period": "act"}, 1)
                    await self.cmd("102_64", {"init": "act"}, 1)

            # Ping
            if self.ac_ping > self.ac_ping_max:
                self.ac_init = 0
            else:
                self.ac_init = 1

            # Wait
            await asyncio.sleep(self.ac_ping_wait)

    def store_date(self, msg, data, store):
        binary_string = msg.get_binary()
        try:
            idx = 0
            for _data in data:
                offset = _data["offset"]
                length = _data["sz"]
                result = binary_string[offset:(offset + length)]
                result_int = int(result, 2)
                if _data['name'] in _data_template:
                    try:
                        result_int = _data_template[_data['name']][result_int]
                    except Exception as e:
                        pass

                store[idx] = result_int
                idx += 1
        except Exception as e:
            log.error(f"{e}")

    # def store_date(self, msg, data, store):
    #     binary_string = msg.get_binary()
    #     try:
    #         for idx, _data in enumerate(data):
    #             offset = _data["offset"]
    #             length = _data["sz"]
    #             # Use bit manipulation to extract the required bits
    #             mask = (1 << length) - 1
    #             result_int = (int(binary_string, 2) >> offset) & mask
    #             result_int = _data_template.get(_data['name'], {}).get(result_int, result_int)
    #             store[idx] = result_int
    #     except Exception as e:
    #         log.error(f"{e}")


    # def info_data(self):
    #     for _data in _Data_102_0:
    #         prop_name = _data["name"]
    #         prop_val = _data["val"]
    #         log.info(f"  {prop_val}   - {prop_name}")

    async def cmd(self, pkt_name, opt_cmd_list=None, wait=0.01):
        # ["101_0", {"temp_indoor_set": 23}]
        # debug
        # log.debug(f"")
        # log.debug(f"")
        # log.debug(f"CMD: {pkt_name} : {opt_cmd_list}")
        try:
            op_name = pkt_name

            op_cmd = opt_cmd_list
            if opt_cmd_list is None:
                op_cmd = {}

            # "102_64":   {"send_sz": 0,   "recv_sz": 136, },
            if op_name == "101_0":
                opt_ata = _Setting_101_0
            elif op_name == "102_0":
                opt_ata = _Setting_102_0
            elif op_name == "102_64":
                opt_ata = _Setting_102_64
            elif op_name == "10_4":
                opt_ata = _Setting_10_4
            elif op_name == "7_1":
                opt_ata = _Setting_7_1
            elif op_name == "30_0":
                opt_ata = _Setting_30_0
            else:
                return

            cmd_data = _Data_CMD[op_name]
            # Generate list of commands
            msg_data = [0] * cmd_data["send_sz"]
            # debug
            # log.debug(f"msg_data_template:   {msg_data}")

            # check if meessage len more than 0bit
            if op_name == "101_0":
                msg_data[61] = 1  # set bit 61 to 1, protocol needed
            if len(msg_data) > 0:
                for key, value in op_cmd.items():
                    _data = opt_ata[key]
                    if type(value) is int:  # if int, convert to binary string + 1bit control bit for each setting
                        prop_sz = _data["sz"] - 1
                        prop_val = f'{value:0>{prop_sz}b}1'
                    else:
                        prop_val = _data["prop"][value]  # get setting value from _Data

                    # debug
                    # log.debug(f"{key}: {prop_val}")
                    # make binary string with data bit
                    for i in range(len(prop_val)):
                        msg_data[_data["offset"] + i] = int(prop_val[i])

            # debug
            # log.debug(f"msg_data:   {msg_data}")

            # start build message
            mdata = bytearray()
            mdata.extend(bytes([0xF4, 0xF5]))  # F4F5 header
            mdata.append(0x00)  # 0x00 request
            mdata.append(0x40)  # padding byte

            # convert bits to bytes
            bits = msg_data
            byte_list = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
            # log.debug(f"byte_list:   {byte_list}")
            byte_data = struct.pack("b" * len(byte_list), *byte_list)
            # log.debug(f"byte_data:   {byte_data}")

            # add data to message
            mdata.append(len(byte_data) + 11)  # packet length
            mdata.extend(bytes([0x00, 0x00, 0x01, 0x01, 0xFE, 0x01, 0x00, 0x00]))  # padding bytes

            # packet type and sub-type
            pkt_type = pkt_name.split("_")
            mdata.extend(bytes([int(pkt_type[0]), int(pkt_type[1])]))  # packet type and sub-type, [0x65, 0x00]

            # padding byte
            mdata.append(0x00)  # padding byte for request
            mdata.extend(byte_data)  # data

            # CRC Calculation
            crc_data = mdata[2:]
            crc_sum = 0
            for crc_val in crc_data:
                crc_sum = crc_sum + crc_val
            mdata.extend(struct.pack(">h", crc_sum))  # CRC

            # Finish with footer
            mdata.extend(bytes([0xF4, 0xFB]))  # F4F5 footer

            # log.debug(f" Data hex: {hexh(mdata)}")
            # if wait is not None:
            #     await self.ac_swriter.awrite(mdata)
            #     await asyncio.sleep(wait)
            # else:
            #     launch(self.ac_swriter.awrite, mdata)
            #     await asyncio.sleep(0.01)

            await self.ac_swriter.awrite(mdata)
            await asyncio.sleep(wait)

        except Exception as e:
            log.error(f"CMD: {e} - {pkt_name} : {opt_cmd_list}")


def find(s, ch='1'):
    return [i for i, ltr in enumerate(s) if ltr == ch]

class Message():
    def __init__(self, mdata):
        self.mdata = mdata
        self.packet_info_length = 11
        self.packet_msg_length = -1
        self.crc = -1

    def unpack_mdata(self):
        self.header =           self.mdata[0:2]    # F4F5 header
        self.paket_type =       self.mdata[2]      # (0x01 response, 0x00 request)
        self.padding_byte_1 =   self.mdata[3]      # (0x40) padding byte _1
        self.packet_length =    self.mdata[4]      # (packet length) plus (9) [static F4F5014049..064FF4FB]
        self.padding_byte_2 =   self.mdata[5:13]   # (01 00 FE 01 01 01 01 00) padding bytes _2
        self.msg_packet_type =  self.mdata[13]     # 0x66 = 102 - packet type.  6600 - (0x66 0x00) packet type and sub-type (102 sub 0)
        self.msg_sub_type =     self.mdata[14]     # 0x00 =  00 - packet sub-type.
        self.padding_byte_3 =   self.mdata[15]     # (0x01) padding byte _3
        self.msg_data =         self.mdata[16:-4]  # [...] data
        self.msg_sum =          self.mdata[-4:-2]  # 064F - (0x06 0x4F) sum bit to bit of previous bytes, header excluded
        self.footer =           self.mdata[-2:]    # F4FB - (0xF4 0xFB) footer

    def info_msg(self):
        direction = "Response: from AC" if self.paket_type == 0x01 else "Request: to AC"
        log.info(f" {direction}")
        log.info(f" Data hex: {hexh(self.mdata)}")
        log.info(f" header:             {hexh(self.header)}")
        log.info(f" paket_type: dec:    {self.paket_type} :  {hex(self.paket_type)}")
        log.info(f" padding_byte_1:     {hex(self.padding_byte_1)}")
        log.info(f" packet_length:      {hex(self.packet_length)}")
        log.info(f" padding_byte_2:     {hexh(self.padding_byte_2)}")
        log.info(f" m_packet_type: dec: {self.msg_packet_type} : {hex(self.msg_packet_type)} - m_sub_type: dec: {self.msg_sub_type} : {hex(self.msg_sub_type)}")
        log.info(f" padding_byte_3:     {hex(self.padding_byte_3)}")
        log.info(f" msg_data:           {hexh(self.msg_data)}")
        log.info(f" msg_sum:            {hexh(self.msg_sum)}")
        log.info(f" footer:             {hexh(self.footer)}")
        log.info(f"")
        log.info(f" CRC:                {self.crc} == {int(hexh(self.msg_sum, ''), 16)} ")
        log.info(f" Data size:          {self.packet_msg_length} bit")
        log.info(f" Data binary: {self.get_binary()}")
        log.info(f" 0ffset where bit == 1 :    {find(self.get_binary(), '1')}")

    def get_binary(self):
        bytes_data = b""
        try:
            bytes_data = bytes(self.msg_data)
            # first create byte string after converterto int and then convert to binary string
            binary_string = f'{int(hexh(bytes_data, ""), 16):0>{self.packet_msg_length}b}'
        except Exception as e:
            log.error(f"get_binary: {e} - {hexh(bytes_data)}")
            return ""
        return binary_string

    def step_2_check_crc(self):
        # CRC Calculation
        crc_data = self.mdata[2:-4]
        crc_msg =  self.mdata[-4:-2]
        crc_int = int(hexh(crc_msg, ''), 16)
        crc_sum = 0
        for crc_val in crc_data:
            crc_sum = crc_sum + crc_val

        if crc_int == crc_sum:
            self.crc = crc_sum

        # log.debug(f" crc_calc:  {crc_sum},  {hexh(struct.pack('>h', crc_sum))}")
        # log.debug(f" crc_msg:   {crc_int},  {hexh(crc_msg)}")
        # log.debug(f" CRC:  {crc_sum} == {crc_int} ")


    def step_1_check_len(self):
        packet_length = self.mdata[4]
        packet_length_calc = len(self.mdata) - 9
        packet_info_length = 11

        # packet_length bytes plus 9 static F4F5014049..064FF4FB)
        if packet_length == packet_length_calc:
            self.packet_msg_length = (packet_length - packet_info_length) * 8  # (73 - 11) * 8 #  = 496

        # log.debug(f" packet_length:      {packet_length_calc} == {packet_length} :  {hex(packet_length)}")
