
from scrivo import logging
log = logging.getLogger("CORE")


def call_try(elog=log.error):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                elog("error: {}".format(e))
                pass
        return applicator
    return decorate


@call_try()
def encode_UTF8(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return data


@call_try()
def decode_UTF8(data):
    if isinstance(data, int):
        return data
    if not isinstance(data, str):
        data = data.decode('utf-8')
    return data


def decode_payload(func):
    def decorator(self, msg):
        if isinstance(msg.payload, bytes):
            msg.payload = msg.payload.decode('utf-8')
        return func(self, msg)
    return decorator


class DataClassArg:
    name = None

    def __init__(self, *args, **kwargs):
        for key in args:
            setattr(self, key, None)
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __call__(self, config_dict):
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def __str__(self):
        return ', '.join(f'{k}={v}' for k, v in self.__dict__.items())

    def __repr__(self):
        return 'DataClassArg({})'.format(', '.join(['{}={}'.format(k, repr(v)) for k, v in self.__dict__.items()]))

    def a_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, config_dict):
        for key, value in config_dict.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        return cls


# scale(10, (0, 100), (80, 30))
def scale(val, src, dst):
    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]


def hexh(data,  sep=' '):
    try:
        data = f'{sep}'.join('{:02x}'.format(x) for x in data)
    except Exception as e:
        log.debug("error: HEX: {}".format(e))
    return data


# value: число, у которого необходимо считать бит
# bit: номер бита, состояние которого необходимо считать.
def get_bit(value, bit):
    return (value & (1 << bit)) == 1

def set_bit(value, bit, bit_value):
    if bit_value:
        return value | (1 << bit)
    else:
        return value & ~(1 << bit)


def secret(val, result=False, _secret="!secret "):
    # if isinstance(val, str) and val.startswith(_secret):
    try:
        search = val.split(_secret, 1)[-1]
        with open("./secret") as f:
            for line in f:
                if line.startswith(search):
                    result = line.split(":")[-1].rstrip()
    except Exception as e:
        log.error(f"Error: secret file: {e}")
    return result







