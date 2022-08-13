from scrivo.loader.loader import Load
from scrivo_uwebsockets.server import WebsocketServer

from scrivo.dev import asyncio
import json

from scrivo import logging
log = logging.getLogger("WS:server")


class Runner(Load):
    wss = None

    async def _activate(self):

        ws_cfg = await self.uconf.call("select_one", "ws_server", "default")
        port = 8083
        if ws_cfg and "port" in ws_cfg:
            port = ws_cfg["port"]

        self.wss = WebsocketServer(port)
        self.wss.on_message = self.on_message

        self.wss.start()
        await asyncio.sleep(1)


    async def on_message(self, ws, msg):
        # response = {
        #     "error" : None,
        #     "result" : {"id" : -1}
        # }

        # await ws.send(json.dumps(response))
        response_rpc = await self.core.rpc.call(msg.decode())
        if response_rpc:
            await ws.send(response_rpc)
        else:
            response = {
                "error": None,
                "result": {"id": -1}
            }
            await ws.send(json.dumps(response))

        # echo websocket
        # await ws.send(msg.decode())



