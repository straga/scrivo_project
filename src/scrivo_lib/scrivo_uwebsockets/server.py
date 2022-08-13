from scrivo.dev import asyncio
from .protocol import Websocket
from .handshake import hash_key

from scrivo.dev import _aclose
from scrivo.dev import _awrite
from scrivo.dev import launch

from scrivo import logging
log = logging.getLogger("WS:server")
# log.setLevel(logging.DEBUG)


class WebsocketServer:

    def __init__(self,  port, host="0.0.0.0"):

        self.host = host
        self.port = port

        self.clients = []
        self.id_client = 0
        self._run = False
        self.on_message = None


    async def _new_client_(self, reader, writer):
        addr = writer.get_extra_info('peername')
        log.info("Server: {} <- Client {}".format(self.port, addr))
        ip = addr[0]

        connect = WebSocketConnect(self.id_client, reader, writer, self)

        self.id_client += 1
        client = {
            'id': self.id_client,
            'ip': ip,
            'connect': connect
        }
        self.clients.append(client)
        launch(connect.handshake)


    def get_client(self, id_client):
        for client in self.clients:
            if client['id'] == id_client:
                return client

    async def client_remove(self, id_client):
        client = self.get_client(id_client)
        if client:
            if client["connect"].websocket:
                await client["connect"].websocket.close()
            self.clients.remove(client)

    def start(self):
        if not self._run:
            loop = asyncio.get_event_loop()
            loop.create_task(asyncio.start_server(self._new_client_, self.host, self.port))

            log.info("RUN = {}:{}".format(self.host, self.port))
            self._run = True
        else:
            log.info("Already RUN = {}:{}".format(self.host, self.port))
        return True


class WebSocketConnect:

    def __init__(self, c_id, reader, writer, server):

        self.c_id = c_id
        self.reader = reader
        self.writer = writer
        self.valid_client = False
        self.server = server
        self.websocket = None

    async def on_message(self, msg):
        if self.server.on_message:
            await self.server.on_message(self.websocket, msg)

    async def handshake(self):
        webkey = None

        while True:
            line = None
            try:
                line = await self.reader.readline()
            except Exception as err:
                log.error(err)
                pass

            #log.debug("WS: line={}".format(line))

            if line == b"\r\n" or line == b"":
                log.debug("WS: line={}".format(line))
                break
            if line.startswith(b'Sec-WebSocket-Key'):
                webkey = line.split(b":", 1)[1]
                webkey = webkey.strip()

        if webkey:
            respkey = hash_key(webkey)

            resp = "" \
                    "HTTP/1.1 101 Switching Protocols\r\n"  \
                    "Upgrade: websocket\r\n" \
                    "Connection: Upgrade\r\n" \
                    "Sec-WebSocket-Accept: {}\r\n"\
                    "\r\n".format(respkey)

            await _awrite(self.writer, resp)

            self.valid_client = True
            log.info("Finished websocket handshake")
            self.websocket = Websocket(self.reader, self.writer, on_message=self.on_message)

            self.websocket.open()

            log.info("Wait Data")
            await self.websocket.recv()
            await self.drop_me()

            log.info("Disconnect: {}".format(self.c_id))

        else:
            await self.drop_me()
            log.error("Not a websocker request")

        # anyway close
        await _aclose(self.writer)

    async def drop_me(self):
        await self.server.client_remove(self.c_id)







