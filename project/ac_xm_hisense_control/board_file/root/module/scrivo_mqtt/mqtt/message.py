
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
        self._payload_size = None
        self._payload = payload
        self._done = False

    @property
    def payload(self):
        if not self._done:
            self.desilization()
        return self._payload

    @property
    def payload_size(self):
        if not self._done:
            self.desilization()
        return self._payload_size

    def desilization(self):

        if isinstance(self._payload, (list, tuple, dict)):
            self._payload = json.dumps(self._payload).encode('utf-8')

        elif isinstance(self._payload, (int, float)):
            self._payload = str(self._payload).encode('ascii')

        elif isinstance(self._payload, str):
            self._payload = self._payload.encode('utf-8')

        elif isinstance(self._payload, bool):
            self._payload = str(self._payload).encode('ascii')

        elif self._payload is None:
            self._payload = b''

        if self._payload_size is None:
            try:
                self._payload_size = len(self._payload)
            except Exception as e:
                log.error(f"get_size: {e} - {self._payload}")
                self._payload = "error".encode('utf-8')
                self._payload_size = len(self._payload)

        log.debug(f"MSG: {self.topic} -> size: {self._payload_size}")

        if self._payload_size > 268435455:
            log.warning('Message too big')
            self._payload = b''
            self._payload_size = len(b'')

        self._done = True

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
