# Copyright (c) 2020 Viktor Vorobjov

from scrivo.dev import asyncio
import struct
from scrivo.dev import launch

from .handler import MQTTHandler
from .transport import MqttTransport

from scrivo import logging
log = logging.getLogger("MQTT")


class MQTTConnect:
    def __init__(self, cleint, addr="127.0.0.1", port=1883):

        self.addr = addr
        self.port = port

        self.client = cleint
        self.transport = None

    async def create_connect(self):
        try:
            log.info(f"[CONNECT] Open - addr:{self.addr} port:{self.port}")
            self.client.open_status = 1

            reader, writer = await asyncio.open_connection(self.addr, self.port)
            self.transport = MqttTransport(reader, writer)
            log.info("[CONNECT] Opening")

            launch(self._wait_msg)
            log.info("Wait Message: Start")

            log.info("[CONNECT] Action")
            await self.client.connect_action()
        except Exception as e:
            self.client.open_status = 0
            log.debug(f"ERROR: Connect Open: {e}")
            return

    async def _wait_msg(self):

        handler = MQTTHandler(self.client).handler
        while self.transport.reader:
            try:
                byte = await self.transport.reader.read(1)
                if byte is None:
                    return
                if byte == b'':
                    raise OSError(-1)

                m_type = struct.unpack("!B", byte)[0]
                log.debug("Wait Message: while")
                log.debug(f"   -: m_type: {m_type}")

                m_raw = await self._read_packet()
                # log.debug("   -: m_raw: {}".format(m_raw))

                await handler(m_type, m_raw)

            except Exception as e:
                log.debug(f"Error: wait_msg: {e}")
                await self.close("Wait Message: error")
        log.debug("Wait Message: stop")

    async def _read_packet(self):
        remaining_count = []
        remaining_length = 0
        remaining_mult = 1

        while True:
            byte, = struct.unpack("!B", await self.transport.reader.read(1))
            remaining_count.append(byte)

            if len(remaining_count) > 4:
                log.warning('PROTOCOL ERROR: RECV MORE THAN 4 bytes for remaining length.')
                return None

            remaining_length += (byte & 127) * remaining_mult
            remaining_mult *= 128

            if byte & 128 == 0:
                break

        packet = b''
        while remaining_length > 0:
            chunk = await self.transport.reader.read(remaining_length)
            remaining_length -= len(chunk)
            packet += chunk
        return packet

    async def close(self, triger=None):
        try:
            self.client.open_status = 0
            self.client.broker_status = 0
            self.transport.reader = None
            await self.transport._aclose()
        except Exception as e:
            log.debug(f"[CONNECT] Close: Error: {e}")

        self.client.on_disconnect(self.client)
        await asyncio.sleep(5)
        log.debug(f"[CONNECT] Close: {triger}")
