
from scrivo.module import Module
from scrivo.platform import launch
from scrivo.dev import DataClassArg

from .mqtt_as import MQTTClient, config
import asyncio
import json

from scrivo import logging
log = logging.getLogger("MQTT")
log.setLevel(logging.DEBUG)


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

class Message(DataClassArg):
    topic = ""
    payload = ""
    retain = False

class MqttPub:
    def __init__(self, topic, qos=0, retain=False, pub=True):
        self.topic = topic
        self.qos = qos
        self.retain = retain
        self.pub = pub

class Runner(Module):
    alive = False
    lock = asyncio.Lock()
    event = asyncio.Event()

    def activate(self, props):
        self.sub_tpc_obj = []
        self.brocker_name = "MQTT"
        self.blk_list = ["MQTT", "local"]

        log.debug(f"Add Config params to module: {props.configs}")

        self.cfg = None
        for configs in props.configs:
            self.cfg = Config.from_dict(configs)

        self.client_topic = self.cfg.topic

        config['server'] = '192.168.100.240'  # Change to suit e.g. 'iot.eclipse.org'

        config['subs_cb'] = self.mqtt_on_message
        config['connect_coro'] = self.on_connect
        config["will"] = (f"{self.client_topic}/status", "offline")

        MQTTClient.DEBUG = True  # Optional: print diagnostic messages

        self.client_sub_topic = f"{self.client_topic}/cmd/#"

        # subscribe on all messange in local MBUS
        self.sub_h(topic="/#", func="mbus_on_message")

        self.client = MQTTClient(config)



        launch(self.mqtt_publish)

    async def mqtt_publish(self):
        await self.client.connect()

        while True:
            await self.event.wait()
            for k in list(self.mbus.mpub.keys()):
                msg = self.mbus.mpub[k]
                if hasattr(msg, "mqtt") and msg.mqtt.pub:
                    await self.publish(msg.mqtt.topic, msg.payload, msg.retain)
                    msg.mqtt.pub = False

            self.event.clear()

    async def publish(self, topic, payload, retain=False):
        async with self.lock:
                if isinstance(payload, (list, tuple, dict)):
                    payload = json.dumps(payload)

                if isinstance(payload, (int, float)):
                    payload = str(payload).encode('ascii')
                elif isinstance(payload, str):
                    payload = payload.encode('utf-8')
                elif isinstance(payload, bool):
                    payload = str(payload).encode('ascii')
                elif payload is None:
                    payload = b''
                else:
                    payload = payload

                await self.client.publish(topic, payload, retain)



    async def on_connect(self, client):

        log.info("MQTT: Connected to broker")

        await self.client.subscribe(self.client_sub_topic, 0)

        self.alive = True
        self.mbus.pub_h("mqtt", "connect")
        await self.publish(f"{self.client_topic}/status", "online", retain=True)

        log.info("MQTT: Connected done")


    # Publish from mqtt to mbus
    def mqtt_on_message(self, topic, payload, retained):

        try:
            print_topic = topic.decode('utf-8')
        except UnicodeDecodeError as exc:
            log.warning('[INVALID CHARACTER IN TOPIC] {} - {}'.format(topic, exc))
            print_topic = topic

        #log.info(f"MQTT: t: {print_topic}, p: {payload}, r: {retained}")

        tpc_list = print_topic.rsplit(self.client_topic + "/", 1)
        self.core.mbus.pub_h(tpc_list[-1], payload, brk=self.brocker_name, retain=retained)

    # # Publish from mbus to mqtt
    def mbus_on_message(self, msg):
        log.info(
            f"MBUS --> MQTT: t: {msg.topic},  k: {msg.key}, p: {msg.payload} : {msg.properties}")
        broker = msg.properties.get('brk', None)
        retain = msg.properties.get('retain', False)
        direct = msg.properties.get('direct', False)
        #properties = msg.properties.get('properties', {})

        if broker not in self.blk_list:

            topic = "{}/{}".format(msg.topic, msg.key)
            if msg.topic is None:
                topic = "{}".format(msg.key)

            if not direct:
                topic = "{}/event/{}".format(self.client_topic, topic)
            else:
                topic = "{}".format(topic)

            mpub_msg = self.mbus.mpub.get(f"{msg.topic}/{msg.key}", None)
            if mpub_msg is not None:
                mpub_msg.mqtt = MqttPub(topic, qos=msg.qos, retain=retain, pub=True)
                self.event.set()


    def _pub_msg(self, topic, payload, retain=False, qos=0, **kwargs):

        direct = kwargs.get('direct', False)
        properties = kwargs.get('properties', {})

        if not direct:
            topic = "{}/event/{}".format(self.client_topic, topic)
        else:
            topic = "{}".format(topic)

        return Message(topic=topic, payload=payload, retain=retain, qos=qos, **properties)


    async def apub_msg(self, topic, payload, retain=False, qos=0, **kwargs):
        pub_msg = self._pub_msg(topic=topic, payload=payload, retain=retain, qos=qos, **kwargs)
        await self.publish(pub_msg.topic, pub_msg.payload, pub_msg.retain)


