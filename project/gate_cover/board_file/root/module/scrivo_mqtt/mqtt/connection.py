# Copyright (c) 2020 Viktor Vorobjov
import gc
import asyncio
import struct
from scrivo.platform import launch

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
            gc.collect()
            reader, writer = await asyncio.wait_for(asyncio.open_connection(self.addr, self.port), 5)

            log.info("[CONNECT] Opening")

            self.transport = MqttTransport(reader, writer)

            log.info("[Trasport] OK")

            launch(self.mqtt_wait_msg)
            log.info("Wait Message: Start")

            log.info("[CONNECT] Action")
            await self.client.connect_action()

        except asyncio.TimeoutError as e:
            self.client.open_status = 0
            log.error(f"ERROR: {e}")

        except Exception as e:
            self.client.open_status = 0
            log.error(f"ERROR: Connect Open: {e}")


    async def mqtt_wait_msg(self):
        handler = MQTTHandler(self.client).handler
        while self.transport.reader:
            try:
                log.debug("Wait Message: while")
                byte = await self.transport.reader.read(1)
                if byte is None:
                    return
                if byte == b"":
                    raise OSError(f"byte: {byte}")

                m_type = struct.unpack("!B", byte)[0]
                log.debug(f"   -: m_type: {m_type}")

                m_raw = await self._read_packet()
                # log.debug("   -: m_raw: {}".format(m_raw))

                await handler(m_type, m_raw)

            except Exception as e:
                log.debug(f"  Error: wait_msg: {e}")
                await self.close("Wait Message: error")
                break
        log.debug("Wait Message: stop")

    async def _read_packet(self):
        remaining_count = []
        remaining_length = 0
        remaining_mult = 1

        while True:
            (byte,) = struct.unpack("!B", await self.transport.reader.read(1))
            remaining_count.append(byte)

            if len(remaining_count) > 4:
                log.warning(
                    "PROTOCOL ERROR: RECV MORE THAN 4 bytes for remaining length."
                )
                return None

            remaining_length += (byte & 127) * remaining_mult
            remaining_mult *= 128

            if byte & 128 == 0:
                break

        packet = b""
        while remaining_length > 0:
            chunk = await self.transport.reader.read(remaining_length)
            remaining_length -= len(chunk)
            packet += chunk
        return packet

    async def close(self, triger=None):
        self.client.broker_status = 0

        if self.transport is not None:
            self.transport.reader = None
            try:
                await self.transport._aclose()
                self.client.on_disconnect(self.client)
            except Exception as e:
                log.debug(f"[CONNECT] Close: Error: {e}")

        await asyncio.sleep(5)
        self.client.open_status = 0
        log.debug(f"[CONNECT] Close: {triger}")
