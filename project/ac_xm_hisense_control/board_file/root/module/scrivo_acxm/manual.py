
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("AC_XM")


hex_string = "f4 f5 01 40 49 01 00 fe 01 01 01 01 00 66 00 01 00 00 00 18 1b 1b 80 80 00 01 01 00 00 00 00 00 00 00 00 00 00 00 05 00 00 00 00 00 1d 17 3e 47 00 00 ec 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 04 ee f4 fb"

def find(s, ch='1'):
    return [i for i, ltr in enumerate(s) if ltr == ch]

def hexh(data, sep=' '):
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


byte_array = bytes.fromhex(hex_string.replace(" ", ""))

msg = Message(byte_array)

msg.step_1_check_len()
msg.step_2_check_crc()
msg.unpack_mdata()
msg.info_msg()

bin_string = msg.get_binary()

_Data_102_0 = [
    {"name": "wind_status",                      "offset": 0,   "sz": 8, "info": "0 - 18: Super High Wind, "},
    {"name": "sleep_status",                     "offset": 8,   "sz": 8, "info": "1"},
    {"name": "mode_status",                      "offset": 16,  "sz": 4, "info": "2"},
    {"name": "run_status",                       "offset": 20,  "sz": 1, "info": "3"},
    {"name": "direction_status",                 "offset": 22,  "sz": 2, "info": "4 - wind direction"},
    {"name": "indoor_temperature_setting",       "offset": 24,  "sz": 8, "info": "5"},
    {"name": "indoor_temperature_status",        "offset": 32,  "sz": 8, "info": "6"},
    {"name": "indoor_pipe_temperature",          "offset": 40,  "sz": 8, "info": "7"},
    {"name": "indoor_humidity_setting",          "offset": 48,  "sz": 8, "info": "8"},
    {"name": "indoor_humidity_status",           "offset": 56,  "sz": 8, "info": "9"},
    {"name": "somatosensory_temperature",        "offset": 64,  "sz": 8, "info": "10"},
    {"name": "somatosensory_compensation",       "offset": 72,  "sz": 5, "info": "11"},
    {"name": "somatosensory_compensation_ctrl",  "offset": 77,  "sz": 3, "info": "12"},
    {"name": "temperature_compensation",         "offset": 80,  "sz": 5, "info": "13"},
    {"name": "temperature_Fahrenheit",           "offset": 86,  "sz": 1, "info": "14 - Fahrenheit display"},
    {"name": "timer",                            "offset": 88,  "sz": 8, "info": "15"},
    {"name": "hour",                             "offset": 96,  "sz": 8, "info": "16"},
    {"name": "minute",                           "offset": 104, "sz": 8, "info": "18"},
    {"name": "poweron_hour",                     "offset": 112, "sz": 5, "info": "19"},
    {"name": "poweron_minute",                   "offset": 120, "sz": 6, "info": "20"},
    {"name": "poweron_status",                   "offset": 127, "sz": 1, "info": "21"},
    {"name": "poweroff_hour",                    "offset": 128, "sz": 5, "info": "22"},
    {"name": "poweroff_minute",                  "offset": 136, "sz": 6, "info": "23"},
    {"name": "poweroff_status",                  "offset": 143, "sz": 1, "info": "24"},
    {"name": "drying",                           "offset": 144, "sz": 4, "info": "25"},
    {"name": "wind_door",                        "offset": 148, "sz": 4, "info": "26"},
    {"name": "up_down",                          "offset": 152, "sz": 1, "info": "27"},
    {"name": "left_right",                       "offset": 153, "sz": 1, "info": "28"},
    {"name": "nature",                           "offset": 154, "sz": 1, "info": "29 - natural wind"},
    {"name": "heat",                             "offset": 155, "sz": 1, "info": "30 - heating wind"},
    {"name": "low_power",                        "offset": 156, "sz": 1, "info": "31 - energy saving"},
    {"name": "low_electricity",                  "offset": 157, "sz": 1, "info": "32 - eco - energy saving"},
    {"name": "efficient",                        "offset": 158, "sz": 1, "info": "33"},
    {"name": "dual_frequency",                   "offset": 159, "sz": 1, "info": "34"},
    {"name": "dew",                              "offset": 160, "sz": 1, "info": "35"},
    {"name": "swap",                             "offset": 161, "sz": 1, "info": "36"},
    {"name": "indoor_clear",                     "offset": 162, "sz": 1, "info": "37"},
    {"name": "outdoor_clear",                    "offset": 163, "sz": 1, "info": "38"},
    {"name": "smart_eye",                        "offset": 164, "sz": 1, "info": "39"},
    {"name": "mute",                             "offset": 165, "sz": 1, "info": "40 - quite mode"},
    {"name": "voice",                            "offset": 166, "sz": 1, "info": "41"},
    {"name": "smoke",                            "offset": 167, "sz": 1, "info": "42"},
    {"name": "back_led",                         "offset": 168, "sz": 1, "info": "43"},
    {"name": "display_led",                      "offset": 169, "sz": 1, "info": "44"},
    {"name": "indicate_led",                     "offset": 170, "sz": 1, "info": "45"},
    {"name": "indoor_led",                       "offset": 171, "sz": 1, "info": "46"},
    {"name": "filter_reset",                     "offset": 172, "sz": 1, "info": "47"},
    {"name": "left_wind",                        "offset": 173, "sz": 1, "info": "48"},
    {"name": "right_wind",                       "offset": 174, "sz": 1, "info": "49"},
    {"name": "indoor_electric",                  "offset": 175, "sz": 1, "info": "50"},
    {"name": "auto_check",                       "offset": 176, "sz": 1, "info": "51"},
    {"name": "time_laps",                        "offset": 177, "sz": 1, "info": "52"},
    {"name": "rev23",                            "offset": 178, "sz": 4, "info": ""},
    {"name": "sample",                           "offset": 182, "sz": 1, "info": ""},
    {"name": "indoor_eeprom",                    "offset": 183, "sz": 1, "info": ""},
    {"name": "indoor_temperature_sensor",        "offset": 184, "sz": 1, "info": ""},
    {"name": "indoor_temperature_pipe_sensor",   "offset": 185, "sz": 1, "info": ""},
    {"name": "indoor_humidity_sensor",           "offset": 186, "sz": 1, "info": ""},
    {"name": "indoor_water_pump",                "offset": 187, "sz": 1, "info": ""},
    {"name": "indoor_machine_run",               "offset": 188, "sz": 1, "info": ""},
    {"name": "indoor_bars",                      "offset": 189, "sz": 1, "info": ""},
    {"name": "indoor_zero_voltage",              "offset": 190, "sz": 1, "info": ""},
    {"name": "indoor_outdoor_communication",     "offset": 191, "sz": 1, "info": ""},
    {"name": "display_communication",            "offset": 192, "sz": 1, "info": ""},
    {"name": "keypad_communication",             "offset": 193, "sz": 1, "info": ""},
    {"name": "wifi_communication",               "offset": 194, "sz": 1, "info": ""},
    {"name": "electric_communication",           "offset": 195, "sz": 1, "info": ""},
    {"name": "eeprom_communication",             "offset": 196, "sz": 1, "info": ""},
    {"name": "rev25",                            "offset": 197, "sz": 3, "info": ""},
    {"name": "eeprom_communication",             "offset": 196, "sz": 1, "info": ""},
    {"name": "compressor_frequency",             "offset": 200, "sz": 1, "info": ""},
    {"name": "compressor_frequency_setting",     "offset": 208, "sz": 8, "info": ""},
    {"name": "compressor_frequency_send",        "offset": 216, "sz": 8, "info": ""},
    {"name": "outdoor_temperature",              "offset": 224, "sz": 8, "info": ""},
    {"name": "outdoor_condenser_temperature",    "offset": 232, "sz": 8, "info": ""},
    {"name": "compressor_exhaust_temperature",   "offset": 240, "sz": 8, "info": ""},
    {"name": "target_exhaust_temperature",       "offset": 248, "sz": 8, "info": ""},
    {"name": "expand_threshold",                 "offset": 256, "sz": 8, "info": ""},
    {"name": "UAB_HIGH",                         "offset": 264, "sz": 8, "info": ""},
    {"name": "UAB_LOW",                          "offset": 272, "sz": 8, "info": ""},
    {"name": "UBC_HIGH",                         "offset": 280, "sz": 8, "info": ""},
    {"name": "UBC_LOW",                          "offset": 288, "sz": 8, "info": ""},
    {"name": "UCA_HIGH",                         "offset": 296, "sz": 8, "info": ""},
    {"name": "UCA_LOW",                          "offset": 304, "sz": 8, "info": ""},
    {"name": "IAB",                              "offset": 312, "sz": 8, "info": ""},
    {"name": "IBC",                              "offset": 320, "sz": 8, "info": ""},
    {"name": "ICA",                              "offset": 328, "sz": 8, "info": ""},
    {"name": "generatrix_voltage_high",          "offset": 336, "sz": 8, "info": ""},
    {"name": "genertarix_voltage_low",           "offset": 344, "sz": 8, "info": ""},
    {"name": "IUV",                              "offset": 352, "sz": 8, "info": ""},
    {"name": "rev46",                            "offset": 352, "sz": 3, "info": ""},
    {"name": "four_way",                         "offset": 363, "sz": 1, "info": ""},
    {"name": "outdoor_machine",                  "offset": 364, "sz": 1, "info": ""},
    {"name": "wind_machine",                     "offset": 365, "sz": 3, "info": ""},
    {"name": "rev47",                            "offset": 368, "sz": 8, "info": ""},
    {"name": "rev48",                            "offset": 376, "sz": 8, "info": ""},
    {"name": "rev49",                            "offset": 384, "sz": 8, "info": ""},
    {"name": "rev50",                            "offset": 392, "sz": 8, "info": ""},
    {"name": "rev51",                            "offset": 400, "sz": 8, "info": ""},
    {"name": "rev52",                            "offset": 408, "sz": 8, "info": ""},
    {"name": "rev53",                            "offset": 416, "sz": 8, "info": ""},
    {"name": "rev54",                            "offset": 424, "sz": 8, "info": ""},
    {"name": "rev55",                            "offset": 432, "sz": 8, "info": ""},
    {"name": "rev56",                            "offset": 440, "sz": 8, "info": ""}

]
_Data_101_0 = _Data_102_0 # same data for setting and data
# if packet type is 102 or 101 and sub type is 0


if msg.msg_packet_type in [102, 101] and msg.msg_sub_type == 0:
    log.info("AC: 102_0")
    for data in _Data_102_0:
        offset = data["offset"]
        sz = data["sz"]
        slice_string = bin_string[offset:offset+sz]
        if slice_string:  # Check if the slice_string is not empty
            val = int(slice_string, 2)
            log.info(f" {val} : {data['name']}, info: {data['info']}")



