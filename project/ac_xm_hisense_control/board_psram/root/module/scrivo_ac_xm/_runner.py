
from scrivo.loader.loader import Load
from scrivo.tools.tool import launch, asyncio, decode_payload
from machine import UART

from .responses import _data_template
from .responses import _Data_CMD
from .responses import _Data_101_0, _Data_102_64, _Data_102_0, _Data_7_1, _Data_10_4, _Data_30_0
from .responses import _Setting_101_0, _Setting_102_64, _Setting_102_0, _Setting_7_1, _Setting_10_4, _Setting_30_0

import struct

from scrivo import logging
log = logging.getLogger("AC_XM")
# log.setLevel(logging.DEBUG)


def find(s, ch='1'):
    return [i for i, ltr in enumerate(s) if ltr == ch]

def hexh(data,  sep=' '):
    try:
        data = f'{sep}'.join('{:02x}'.format(x) for x in data)
    except Exception as e:
        log.error("HEX: {}".format(e))
    return data


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
            binary_string = f'{int(hexh(bytes_data, ""),16):0>{self.packet_msg_length}b}'
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

        log.debug(f" packet_length:      {packet_length_calc} == {packet_length} :  {hex(packet_length)}")


class Runner(Load):

    async def _activate(self):
        print("4")

        self.ac_uart = UART(2, baudrate=9600, tx=14, rx=15)
        self.ac_swriter = asyncio.StreamWriter(self.ac_uart, {})
        self.ac_sreader = asyncio.StreamReader(self.ac_uart)

        self.lock = asyncio.Lock()

        self.store_10_4 = [-1] * len(_Data_10_4)
        self.store_7_1 = [-1] * len(_Data_7_1)
        self.store_30_0 = [-1] * len(_Data_30_0)

        self.store_102 = [-1] * len(_Data_102_0)
        self.store_102_64 = [-1] * len(_Data_102_64)

        self.ac_ping = 0
        self.ac_init = 0
        self.ac_process_run = True
        launch(self.ac_process)

        # launch(self.mqtt_message)
        self.mbus.sub_h("mqtt/#", self.env, "mqtt_act")
        self.mbus.sub_h("ac_control/#", self.env, "ac_act")
        self.mqtt_run = False
        launch(self.ac_run)

    async def ac_run(self):
        while True:
            # log.info(f"START - AC RUN : init: {self.ac_init},  ping: {self.ac_ping}")

            if self.ac_init == 0:
                async with self.lock:
                    self.cmd("10_4", {"init": "act"})
                    await asyncio.sleep(0.2)
                    self.cmd("7_1", {"init": "act"})
                    await asyncio.sleep(0.2)
                    self.cmd("102_64", {"init": "act"})
                    await asyncio.sleep(0.2)
                    self.cmd("30_0", {"init": "act"})
                    await asyncio.sleep(5)
                    # self.ac_ping = 1
            else:
                async with self.lock:
                    self.ac_ping = self.ac_ping + 1
                    self.cmd("30_0", {"period": "act"})
                    await asyncio.sleep(0.2)
                    self.cmd("102_0", {"period": "act"})
                    await asyncio.sleep(1)
                    self.cmd("102_64", {"init": "act"})
                    await asyncio.sleep(1)

            # log.info(f"STOP AC RUN : init: {self.ac_init},  ping: {self.ac_ping}")
            await asyncio.sleep(1)

            if self.ac_ping > 5:
                self.ac_init = 0
            else:
                self.ac_init = 1

    @decode_payload
    async def ac_act(self, msg):
        log.info(f"ac_control: t: {msg.topic},  k: {msg.key}, p: {msg.payload}")

        msg.payload = msg.payload.lower()
        async with self.lock:
            if msg.key == "run_status":
                self.cmd("101_0", {"run_status": msg.payload})

            elif msg.key == "temp_fahrenheit":
                self.cmd("101_0", {"temp_fahrenheit": msg.payload})

            elif msg.key == "up_down":
                self.cmd("101_0", {"up_down": msg.payload})

            elif msg.key == "left_right":
                self.cmd("101_0", {"left_right": msg.payload})

            elif msg.key == "low_electricity":
                if msg.payload == "on":
                    self.cmd("101_0", {"low_electricity": "on", "wind_status": "lower"})
                elif msg.payload == "off":
                    self.cmd("101_0", {"low_electricity": "off"})

            elif msg.key == "turbo":
                self.cmd("101_0", {"turbo": msg.payload})

            elif msg.key == "quiet":
                if msg.payload == "on":
                    self.cmd("101_0", {"mute": "on", "wind_status": "lower"})
                elif msg.payload == "off":
                    self.cmd("101_0", {"mute": "off"})

            elif msg.key == "back_led":
                self.cmd("101_0", {"back_led": msg.payload})

            elif msg.key == "temp_in":
                temperature = int(msg.payload.split('.')[0])
                self.cmd("101_0", {"temp_indoor_set": temperature})

            elif msg.key == "mode_status":
                self.cmd("101_0", {"mode_status": msg.payload})

            elif msg.key == "wind_status":
                self.cmd("101_0", {"wind_status": msg.payload})

            elif msg.key == "swing":
                if msg.payload == "both":
                    self.cmd("101_0", {"left_right": "on", "up_down": "on"})
                elif msg.payload == "off":
                    self.cmd("101_0", {"left_right": "off", "up_down": "off"})



    def cmd(self, pkt_name, opt_cmd_list=None):
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
                    if type(value) is int: # if int, convert to binary string + 1bit control bit for each setting
                        prop_sz = _data["sz"]-1
                        prop_val = f'{value:0>{prop_sz}b}1'
                    else:
                        prop_val = _data["prop"][value]  # get setting value from _Data

                    # debug
                    # log.debug(f"{key}: {prop_val}")
                    # make binary string with data bit
                    for i in range(len(prop_val)):
                        msg_data[_data["offset"]+i] = int(prop_val[i])

            # debug
            # log.debug(f"msg_data:   {msg_data}")

            mdata = bytearray()
            mdata.extend(bytes([0xF4, 0xF5])) # F4F5 header
            mdata.append(0x00) # 0x00 request
            mdata.append(0x40) # padding byte


            bits = msg_data
            byte_list = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
            # log.debug(f"byte_list:   {byte_list}")
            byte_data = struct.pack("b" * len(byte_list), *byte_list)
            # log.debug(f"byte_data:   {byte_data}")


            mdata.append(len(byte_data)+11)  # packet length
            mdata.extend(bytes([0x00, 0x00, 0x01, 0x01, 0xFE, 0x01, 0x00, 0x00]))  # padding bytes
            pkt_type = pkt_name.split("_")
            mdata.extend(bytes([int(pkt_type[0]), int(pkt_type[1])]))  # packet type and sub-type, [0x65, 0x00]
            mdata.append(0x00)  # padding byte for request
            mdata.extend(byte_data)  # data

            crc_data = mdata[2:]
            crc_sum = 0
            for crc_val in crc_data:
                crc_sum = crc_sum + crc_val

            mdata.extend(struct.pack(">h", crc_sum)) # CRC
            mdata.extend(bytes([0xF4, 0xFB]))  # F4F5 footer

            # log.debug(f" Data hex: {hexh(mdata)}")

            launch(self.ac_swriter.awrite, mdata)

        except Exception as e:
            log.error(f"CMD: {e} - {pkt_name} : {opt_cmd_list}")

    def store_date(self, msg, data, store, print_data=False):
        binary_string = msg.get_binary()
        # log.info(f"store_date: {store}")
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


            # if print_data:
            #     log.info(f"  {result_int}   - {_data['name']} - {result} ")


    def info_data(self):
        for _data in _Data_102_0:
            prop_name = _data["name"]
            prop_val = _data["val"]
            log.info(f"  {prop_val}   - {prop_name}")


    async def ac_process(self):
        # self.ac_sniffer_run = False
        # self.ac_process_run = False
        # await asyncio.sleep(1)
        self.ac_process_run = True
        while self.ac_process_run:
            mdata = 0x00
            try:
                # data = b''
                # try:  # wait for response and read it
                #     data = await asyncio.wait_for(self.ac_sreader.read(-1), 1)
                # except asyncio.TimeoutError:  # Mandatory error trapping
                #     pass
                #     # log.error('Panel got timeout')  # Caller sees TimeoutError

                data = await self.ac_sreader.read(-1)
                # log.info(f" RAW: {data}")

                if data != b'':
                    mdata = memoryview(data)
                    # log.info(f" H: {hexh(mdata)}")
                    #
                    # Generate Message Object.
                    msg = Message(mdata)

                    # Check Messaage size. Extract size from mdata and calc with real message size.
                    msg.step_1_check_len()

                    if msg.packet_msg_length > -1:
                        msg.step_2_check_crc()
                        if msg.crc > -1:

                            # Handler for message type ... .
                            # Unpack data from frame
                            msg.unpack_mdata()

                            # debug
                            # msg.info_msg()

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


            except Exception as e:
                log.error(f"recv: e: {e}, H:{hexh(mdata)}, ")

    def mqtt_act(self, msg):

        if msg.payload == "connect":
            if not self.mqtt_run:
                launch(self.mqtt_publish)

    async def mqtt_publish(self):
        self.mqtt_run = True
        mqtt = self.core.env["mqtt"]
        mqtt.mqtt.queue.maxsize = 10

        for _data in _Data_102_0:
            _data["val"] = -1

        for _data in _Data_102_64:
            _data["val"] = -1

        i = 0
        while self.mqtt_run:
            await mqtt.apub_msg(f"ac_status/ping/value", self.ac_init)

            if i == 30:
                i = 0
                idx = 0
                for _data in _Data_102_0:
                    _data["val"] = self.store_102[idx]
                    name = _data["name"]
                    await mqtt.apub_msg(f"ac_status/{name}/value", self.store_102[idx])
                    idx += 1

                idx = 0
                for _data in _Data_102_64:
                    _data["val"] = self.store_102_64[idx]
                    name = _data["name"]
                    await mqtt.apub_msg(f"ac_power/{name}/value", self.store_102_64[idx])
                    idx += 1

            else:
                idx = 0
                for _data in _Data_102_0:
                    # log.info(f"  {_data['val']}   - {self.store_102[idx]}")
                    if _data["val"] != self.store_102[idx]:
                        _data["val"] = self.store_102[idx]
                        name = _data["name"]
                        await mqtt.apub_msg(f"ac_status/{name}/value", self.store_102[idx])
                    idx += 1
            i += 1

            await asyncio.sleep(1)



