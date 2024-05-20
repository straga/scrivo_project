
from scrivo.module import Module
from scrivo.platform import launch
from scrivo.dev import DataClassArg
import asyncio
# import gc

from .mqtt.client import MQTTClient
# from .mqtt_rpc import Rpc

from scrivo import logging
log = logging.getLogger("MQTT")
#log.setLevel(logging.DEBUG)


class Config(DataClassArg):
    name = "Home"
    addr = "127.0.0.1"
    port = 1883
    topic = "dev/home"
    user = None
    pwd = None
    birth = True
    lwt = True
    sub = []
    maxsize = None  # max size of message queue.
    debug = False


class Runner(Module):
    mqtt = None
    alive = False
    cfg = None
    sub_tpc_obj = []
    brocker_name = "MQTT"
    blk_list = ["MQTT", "local"]
    client_topic = None
    client_sub_topic = None

    def activate(self, props):

        log.debug(f"Add Config params to module: {props.configs}")

        for config in props.configs:
            self.cfg = Config.from_dict(config)

        if self.cfg is not None:
            self.client_topic = self.cfg.topic
            self.mqtt = MQTTClient(client_id=self.core.board.board_id,
                                   addr=self.cfg.addr,
                                   port=self.cfg.port,
                                   maxsize=self.cfg.maxsize)

            if self.cfg.debug:
                log.setLevel(logging.DEBUG)

            self.client_sub_topic = f"{self.client_topic}"

            self.mqtt.on_message = self.mqtt_on_message
            self.mqtt.on_connect = self.on_connect
            self.mqtt.on_disconnect = self.on_disconnect
            self.mqtt.on_subscribe = self.on_subscribe

            # Last Will Topic
            if self.cfg.lwt:
                self.mqtt.will_message = self.mqtt.Message(topic=f"{self.client_topic}/status",
                                                           payload="offline",
                                                           retain=True)
            # Birth
            self.mqtt.birth = self.cfg.birth

            # Start MQTT
            self.mqtt.start()

            # subscribe on all messange in local MBUS
            self.sub_h(topic="/#", func="mbus_on_message")

            # RPC
            # self.rpc = Rpc(self.core, self.mqtt, self.mbus)
            # self.sub_tpc_obj.append(self.mqtt.Subscription(topic=f"{self.client_sub_topic}/rpc/#", no_local=True))

            # CMD topic for subscibe
            self.sub_tpc_obj.append(self.mqtt.Subscription(topic=f"{self.client_sub_topic}/cmd/#", no_local=True))

            # SUB for externat dev, define in config
            for sub_db in self.cfg.sub:
                self.sub_tpc_obj.append(
                    self.mqtt.Subscription(topic=sub_db, no_local=True))
        else:
            log.error("Config not found")

    def on_connect(self, client):
        # subscribe will be list of mqtt.Subscription object
        if self.mqtt:
            self.mqtt.subscribe(self.sub_tpc_obj)

            if self.mqtt.birth:
                pub_msg = self.mqtt.Message(topic=f"{self.client_topic}/status", payload="online", retain=True)
                self.mqtt.pub(pub_msg)

        self.alive = True
        self.mbus.pub_h("mqtt", "connect")

    def on_disconnect(self, client):
        self.alive = False
        self.mbus.pub_h("mqtt", "disconnect")

    def on_subscribe(self, client):
        self.mbus.pub_h("mqtt", "subscribe")

    # Publish from mqtt to mbus
    def mqtt_on_message(self, client, topic, payload, qos, properties):
        # user_property = getattr(properties, "user_property", None)
        # if user_property and "rpc" in user_property:
        #     launch(self.rpc.call, topic, payload, properties)
        # else:
        tpc_list = topic.rsplit(self.client_sub_topic + "/", 1)
        self.core.mbus.pub_h(tpc_list[-1], payload, brk=self.brocker_name, **properties.a_dict())

    # Publish from mbus to mqtt
    def mbus_on_message(self, msg):
        # log.debug(f"PUSH: t: {msg.topic},  k: {msg.key}, p: {msg.payload}")
        broker = msg.properties.get('brk', None)
        retain = msg.properties.get('retain', False)
        direct = msg.properties.get('direct', False)
        properties = msg.properties.get('properties', {})

        if broker not in self.blk_list:

            topic = "{}/{}".format(msg.topic, msg.key)
            if msg.topic is None:
                topic = "{}".format(msg.key)

            if not direct:
                topic = "{}/event/{}".format(self.client_topic, topic)
            else:
                topic = "{}".format(topic)

            pub_msg = self.mqtt.Message(topic=topic, payload=msg.payload, retain=retain, qos=0, **properties)
            self.mqtt.pub(pub_msg)

            #launch(self.mqtt.apub_h, pub_msg)
        #await asyncio.sleep(0.01)

    def _pub_msg(self, topic, payload, retain=False, qos=0, **kwargs):

        direct = kwargs.get('direct', False)
        properties = kwargs.get('properties', {})

        if not direct:
            topic = "{}/event/{}".format(self.client_topic, topic)
        else:
            topic = "{}".format(topic)
        # gc.collect()
        return self.mqtt.Message(topic=topic, payload=payload, retain=retain, qos=qos, **properties)


    def pub_msg(self, topic, payload, retain=False, qos=0, **kwargs):
        pub_msg = self._pub_msg(topic, payload, retain, qos, **kwargs)
        self.mqtt.pub(pub_msg)

    async def apub_msg(self, topic, payload, retain=False, qos=0, **kwargs):
        pub_msg = self._pub_msg(topic, payload, retain, qos, **kwargs)
        await self.mqtt.apub_h(pub_msg)


