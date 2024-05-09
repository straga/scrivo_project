
import json
from scrivo.dev import DataClassArg

from scrivo import logging
log = logging.getLogger("MQTT")


class Message:
    def __init__(self, topic, payload, qos=0, retain=False, **kwargs):
        self.topic = topic
        self.qos = qos
        self.retain = retain
        self.dup = False
        self.properties = DataClassArg(**kwargs)

        if isinstance(payload, (list, tuple, dict)):
            payload = json.dumps(payload)

        if isinstance(payload, (int, float)):
            self.payload = str(payload).encode('ascii')
        elif isinstance(payload, str):
            self.payload = payload.encode('utf-8')
        elif isinstance(payload, bool):
            self.payload = str(payload).encode('ascii')
        elif payload is None:
            self.payload = b''
        else:
            self.payload = payload

        try:
            self.payload_size = len(self.payload)
        except Exception as e:
            log.error(f"get_size: {e} - {self.payload}")
            self.payload = "error".encode('utf-8')
            self.payload_size = len(self.payload)

        if self.payload_size > 268435455:
            log.warning('Message too big')
            self.payload = b''
            self.payload_size = len(b'')

    # def __str__(self):
    #     return f"Message(topic={self.topic}, payload={self.payload})"
    #
    # def __repr__(self):
    #     return self.__str__()


class Subscription:
    def __init__(self, topic, qos=0, no_local=False, retain_as_published=False, retain_handling_options=0,
                 subscription_identifier=None):
        self.topic = topic
        self.qos = qos
        self.no_local = no_local
        self.retain_as_published = retain_as_published
        self.retain_handling_options = retain_handling_options

        self.mid = None
        self.acknowledged = False

        # this property can be used only in MQTT5.0
        self.subscription_identifier = subscription_identifier
