from scrivo.dev import Lock
from scrivo.dev import _awrite
from scrivo.dev import _aclose


class MqttTransport:

    def __init__(self, reader, writer):
        self.writer = writer
        self.reader = reader
        self.lock = Lock()

    async def awrite(self, *args, **kwargs):
        async with self.lock:
            return await _awrite(self.writer, *args, **kwargs)

    async def _aclose(self):
        return await _aclose(self.writer)

