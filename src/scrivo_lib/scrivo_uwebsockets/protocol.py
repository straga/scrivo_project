from scrivo.dev import asyncio
import struct
import random

from scrivo.dev import _aclose
from scrivo.dev import _awrite
from scrivo.dev import launch

from scrivo.tools.tool import encode_UTF8

from scrivo import logging
log = logging.getLogger("uWS:protocol")
# log.setLevel(logging.DEBUG)

from collections import namedtuple
URI = namedtuple('URI', ('protocol', 'hostname', 'port', 'path'))

FIN    = 0x80
OPCODE = 0x0f
MASKED = 0x80
PAYLOAD_LEN = 0x7f
PAYLOAD_LEN_EXT16 = 0x7e
PAYLOAD_LEN_EXT64 = 0x7f

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT         = 0x1
OPCODE_BINARY       = 0x2
OPCODE_CLOSE_CONN   = 0x8
OPCODE_PING         = 0x9
OPCODE_PONG         = 0xA

CLOSE_OK                    = 1000
CLOSE_GOING_AWAY            = 1001
CLOSE_PROTOCOL_ERROR        = 1002
CLOSE_DATA_NOT_SUPPORTED    = 1003
CLOSE_BAD_DATA              = 1007
CLOSE_POLICY_VIOLATION      = 1008
CLOSE_TOO_BIG               = 1009
CLOSE_MISSING_EXTN          = 1010
CLOSE_BAD_CONDITION         = 1011


class Websocket:

    is_client = False

    def __init__(self, reader, writer, on_message=None, on_open=None, on_close=None):

        self.reader = reader
        self.writer = writer
        self.ping_data = None

        self.status = False
        self.on_message = on_message
        self.on_open = on_open
        self.on_close = on_close

    def open(self):
        self.status = True

        if self.is_client:
            launch(self.recv)

        if self.on_open:
            self.on_open()

    async def close(self):
        self.status = False
        await _aclose(self.writer)
        if self.on_close:
            self.on_close()


    async def read(self, sz=-1):
        # Read data from socket if some happens, STOP
        data = None
        try:
            data = await self.reader.read(sz)
            data = memoryview(data)
        except Exception as err:
            log.error("read:{}".format(err))
            await self.close()
            pass

        # log.debug("recv sz:{}, data={}".format(sz, data))
        return data


    # RECV
    async def recv(self):
        # recv data from frame while keep alive
        while self.status:
            try:
                fin, opcode, data = await self.read_frame()
                # return fin, opcode, data
            except Exception as err:
                # pass after error, mark keep alive=False, and stop recv data
                log.error("recv:{}".format(err))
                await self.close()
                pass
                break

            # if recv Frame: decode frame

            if opcode == OPCODE_PING:
                opcode_handler = self.ping_received
            elif opcode == OPCODE_PONG:
                opcode_handler = self.pong_received
            elif opcode == OPCODE_CLOSE_CONN:
                opcode_handler = self.message_received_close
            elif opcode == OPCODE_BINARY or opcode == OPCODE_TEXT:
                opcode_handler = self.message_received
            else:
                break

            # Launch coro with handler
            launch(opcode_handler, data)


    # -> RECV handler # Bin # Text
    async def message_received(self, msg):
        if self.on_message:
            await self.on_message(msg)

    # <- SEND
    async def send(self, msg):
        if isinstance(msg, (bytes, bytearray)):
            await self.write_frame(msg, OPCODE_BINARY)
        elif isinstance(msg, str):
            await self.write_frame(msg, OPCODE_TEXT)
        else:
            log.error("Wrong message format")


    # -> Ping
    async def ping_received(self, msg):
        await self.send_pong(msg)

    # <- Pong
    async def send_pong(self, message):
        await self.write_frame(message, OPCODE_PONG)

    # <- Ping
    async def send_ping(self, message=None, timeout=30):
        # msg for ping
        if message is None:
            message = struct.pack("!I", random.getrandbits(32))
        else:
            message = encode_UTF8(message)

        # send ping
        await self.write_frame(message, OPCODE_PING)

        # wait pong with timeout
        try:
            await asyncio.wait_for(self.wait_pong(), timeout)
        except asyncio.TimeoutError:
            log.debug("timeout!: Ping")
            pass

        # check ping/pong data
        if self.ping_data != message:
            log.debug("ping_data wrong!: Ping")
            await self.close()

        # clear ping data for next ping/pong
        self.ping_data = None


    # -- wait while pong clean ping data
    async def wait_pong(self):
        while self.ping_data is None:
            await asyncio.sleep(1)

    # -- after recv ping, send message as pong
    async def pong_received(self, msg):
        self.ping_data = msg
        # await self.send_pong(msg)


    # Close
    @staticmethod
    def serialize_close(code=CLOSE_OK, reason=""):
        reason = encode_UTF8(reason)
        return struct.pack("!H", code) + reason


    async def message_received_close(self, msg):
        length = len(msg)
        code = 1005
        reason = ""
        #parse close
        if length >= 2:
            code = struct.unpack("!H", msg[:2])
            reason = msg[2:].decode("utf-8")

        log.info("Close: code={}, reason={}".format(code, reason))
        msg = self.serialize_close()
        await self.write_frame(msg, OPCODE_CLOSE_CONN)
        await self.close()

    async def close_message(self, code=CLOSE_OK, reason=""):
        msg = self.serialize_close(code, reason)
        await self.write_frame(msg, OPCODE_CLOSE_CONN)
        await self.close()




    # MASK for Message
    @staticmethod
    def apply_mask(data: bytes, mask: bytes) -> bytes:
        return bytes(b ^ mask[i % 4] for i, b in enumerate(data))

    # FRAME
    async def read_frame(self):
        """
        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-------+-+-------------+-------------------------------+
        |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
        |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
        |N|V|V|V|       |S|             |   (if payload len==126/127)   |
        | |1|2|3|       |K|             |                               |
        +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
        |     Extended payload length continued, if payload len == 127  |
        + - - - - - - - - - - - - - - - +-------------------------------+
        |                               |Masking-key, if MASK set to 1  |
        +-------------------------------+-------------------------------+
        | Masking-key (continued)       |          Payload Data         |
        +-------------------------------- - - - - - - - - - - - - - - - +
        :                     Payload Data continued ...                :
        + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
        |                     Payload Data continued ...                |
        +---------------------------------------------------------------+
        """


        # read first 2byte=8bit
        data = await self.read(2)

        # upack to to [b'', b'']
        head1, head2 = struct.unpack("!BB", data)

        # websocket protocol detect
        fin = head1 & FIN > 0
        opcode = head1 & OPCODE
        masked = head2 & MASKED > 0
        length = head2 & PAYLOAD_LEN

        # Client Mask always False
        if not self.is_client and not masked:
            return None

        log.debug("WS: head1={}, head2={}".format(head1, head2))
        log.debug("WS: < recv=(fin={}, opcode={}, masked={}, length={})".format(fin, opcode, masked, length))

        # from head len=7
        # if Extended len 16/64
        # len == 126/127
        # detect lenght bit size
        byte_lenght = None
        if length == 126:
            byte_lenght = 2
            byte_unpack = ">H"
        elif length == 127:
            byte_lenght = 8
            byte_unpack = ">Q"

        if byte_lenght:
            byte_read = await self.read(byte_lenght)
            length = struct.unpack(byte_unpack, byte_read)[0]

        log.debug("lenght: {}".format(length))

        # mask read 4byte = 16bit
        if masked:
            mask_bits = await self.read(4)
            log.debug("mask_bits: {}".format(mask_bits))


        # data - read message
        message_read = await self.read(length)
        # log.debug("RAW MSG: {}".format(message_read))
        log.debug("RAW MSG")

        # if masked decode message use mask bits
        if masked:
            message_read = self.apply_mask(message_read, mask_bits)

        # log.debug("REAL MSG: {}".format(message_read))
        log.debug("REAL MSG")

        return fin, opcode, message_read



    async def write_frame(self, data=None, opcode=OPCODE_TEXT):

        # HEADER byte array
        header = bytearray()
        mask = self.is_client  # messages sent by client are masked

        payload = encode_UTF8(data) # encode str, if not str return as it
        if payload is None:
            log.warning("Wrong message - {}".format(data))
            return False

        # Put head1 in HEADER for Frame bit.
        # Fin | opcode , "{0:b}".format(0b10000000 | 0b1111) = 10001111
        # # PONG = 0xA = 10000000 | 1010 = '10001010'
        # b'\xba@'.hex()
        # 'ba40'
        # "{0:b}".format(0xba40)
        # '1011101001000000'
        head1 = FIN | opcode
        header.append(head1)

        log.debug("HEAD: {}".format(header))

        # Mask - Head2
        head2 = 0b10000000 if mask else 0

        # lenght get payload len
        payload_length = len(payload)

        # Normal payload
        if payload_length < 126:
            header.append(head2 | payload_length)

        # Extended payload
        elif payload_length < 65536:
            header.append(head2 | PAYLOAD_LEN_EXT16)
            header.extend(struct.pack(">H", payload_length))

        # Huge extended payload - May be need skip that for IOT dev
        else:
            header.append(head2 | PAYLOAD_LEN_EXT64)
            header.extend(struct.pack(">Q", payload_length))

        log.debug("HEAD: {}".format(header))

        # Masked message if mask needed
        if mask:  # Mask is 4 bytes
            mask_bits = struct.pack('!I', random.getrandbits(32))
            log.debug("MASK 4bit: {}".format(mask_bits))
            header.extend(mask_bits)
            payload = self.apply_mask(payload, mask_bits)

        # write header and payload as Websocket Frame
        log.debug("HEAD: {}".format(header))
        log.debug("PAYLOAD: {}".format(payload))

        await _awrite(self.writer, header)
        await _awrite(self.writer, payload)

