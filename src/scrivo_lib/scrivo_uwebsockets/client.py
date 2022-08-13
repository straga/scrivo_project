from scrivo.dev import asyncio
from .protocol import Websocket, URI
from .handshake import request_key, hash_key

from scrivo.dev import _awrite


from scrivo import logging
log = logging.getLogger("uWS:client")


class WebsocketClient(Websocket):
    is_client = True


async def connect(protocol="ws", hostname="127.0.0.1", port=8081, path="/",
                  on_open=None,
                  on_message=None,
                  on_close=None):

    # URL decode
    url = URI(protocol=protocol, hostname=hostname, port=port, path=path)


    # Connect to Server
    try:
        log.info("[CONNECT] addr:{} port:{}".format(url.hostname, url.port))
        reader, writer = await asyncio.open_connection(url.hostname, url.port)
    except Exception as e:
        log.debug("ERROR open connect: {}".format(e))
        return

    # Send method Header
    async def send_header(header, *args):

        header = header.format(*args)
        resp = "{}\r\n".format(header)

        log.debug("resp:{}".format(resp))
        await _awrite(writer, resp)

    # Gen Handshake Request KEy
    key = request_key()

    # Send Header over HTTP string by string
    await send_header('GET {} HTTP/1.1', url.path or '/')
    await send_header('Host: {}:{}', url.hostname, url.port)
    await send_header('Connection: Upgrade')
    await send_header('Upgrade: websocket')
    await send_header('Sec-WebSocket-Key: {}', key)
    await send_header('Sec-WebSocket-Version: 13')
    await send_header('Origin: http://{}:{}', url.hostname, url.port)
    await send_header('')

    # Reade from Reaply Websocker Accept Key
    webkey = None
    while True:
        line = None
        try:
            line = await reader.readline()
        except Exception as err:
            log.error(err)
            pass

        log.debug("WS: line={}".format(line))

        if line:
            if line == b"\r\n":
                break
            if line.startswith(b'Sec-WebSocket-Accept'):
                webkey = line.split(b":", 1)[1]
                webkey = webkey.strip().decode()
        else:
            break

    log.debug("WS: webkey={}".format(webkey))


    # Check Hash: Request key and Received key
    # If True return websocket transport
    if webkey and webkey == hash_key(key):
        websocket = WebsocketClient(reader, writer,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_close=on_close)
        websocket.open()
        return websocket
    else:
        log.error("Wrong Key Handshake")

