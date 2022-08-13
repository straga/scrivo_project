
import binascii
import hashlib
import random


def request_key():
    # Sec-WebSocket-Key is 16 bytes of random base64 encoded
    key = binascii.b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1]
    return key.decode()


def hash_key(webkey):
    if isinstance(webkey, str):
        webkey = webkey.encode()
    d = hashlib.sha1(webkey)
    d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    respkey = d.digest()
    respkey = binascii.b2a_base64(respkey)[:-1]
    return respkey.decode()
