from asyncio import Lock
from scrivo.platform import awrite
from scrivo.platform import aclose


class MqttTransport:

    def __init__(self, reader, writer):
        self.writer = writer
        self.reader = reader
        self.lock = Lock()

    async def awrite(self, *args, **kwargs):
        async with self.lock:
            return await awrite(self.writer, *args, **kwargs)

    async def _aclose(self):
        return await aclose(self.writer)

