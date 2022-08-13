
from scrivo.loader.loader import Load
from scrivo.tools.tool import launch

from .mqtt.client import MQTTClient
from .mqtt_rpc import Rpc

from scrivo import logging
log = logging.getLogger("MQTT")

# For DEBUG put the following line in the main.py file
# log = logging.getLogger("MQTT")
# log.setLevel(logging.DEBUG)

class Runner(Load):

    async def _activate(self):
        self.sub_tpc_obj = []
        self.brocker_name = "MQTT"
        self.blk_list = ["MQTT", "local"]
        mqtt_cfg = await self.uconf.call("select", "mqtt_cfg", rtype="model", active=True)

        if mqtt_cfg:

            self.client_topic = self.core.board.topic
            self.mqtt = MQTTClient(client_id=self.core.board.uid, addr=mqtt_cfg.addr, port=mqtt_cfg.port)

            self.client_sub_topic = f"{self.client_topic}"

            self.mqtt.on_message = self.mqtt_on_message
            self.mqtt.on_connect = self.on_connect
            self.mqtt.on_disconnect = self.on_disconnect
            self.mqtt.on_subscribe = self.on_subscribe

            if mqtt_cfg.lwt:
                self.mqtt.will_message = self.mqtt.Message(topic=f"{self.client_topic}/status",
                                                           payload="offline",
                                                           retain=False)
            self.mqtt.birth = mqtt_cfg.birth
            self.mqtt.start()
            self.sub_h(topic="/#", func="mbus_on_message")
            self.rpc = Rpc(self.core, self.mqtt, self.mbus)

            # for own topics
            # self.sub_tpc_obj.append(self.mqtt.Subscription(topic=f"{self.client_sub_topic}/#", no_local=True))
            self.sub_tpc_obj.append(self.mqtt.Subscription(topic=f"{self.client_sub_topic}/rpc/#", no_local=True))
            self.sub_tpc_obj.append(self.mqtt.Subscription(topic=f"{self.client_sub_topic}/cmd/#", no_local=True))
            # for externat dev, define in config
            for sub_db in mqtt_cfg.sub:
                self.sub_tpc_obj.append(
                    self.mqtt.Subscription(topic=sub_db, no_local=True))


    def on_connect(self, client):
        # subscribe will be list of mqtt.Subscription object

        if self.mqtt:
            self.mqtt.subscribe(self.sub_tpc_obj)

            if self.mqtt.birth:
                pub_msg = self.mqtt.Message(topic="{}/status".format(self.client_topic), payload="online", retain=False)
                self.mqtt.pub(pub_msg)

        self.mbus.pub_h("mqtt", "connect")

    def on_disconnect(self, client):
        self.mbus.pub_h("mqtt", "disconnect")

    def on_subscribe(self, client):
        self.mbus.pub_h("mqtt", "subscribe")

    # Publish from mqtt to mbus
    def mqtt_on_message(self, client, topic, payload, qos, properties):

        user_property = getattr(properties, "user_property", None)

        if user_property and "rpc" in user_property:
            launch(self.rpc.call, topic, payload, properties)
        else:
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

    #         self.pub_msg(topic, msg.payload, retain=retain, qos=0, properties=msg.properties)
    #
    # def pub_msg(self, topic, payload, retain=False, qos=0, properties=None):
    #     pub_msg = self.mqtt.Message(topic=topic, payload=payload, retain=retain, qos=qos, **properties)
    #     self.mqtt.pub(pub_msg)

    async def apub_msg(self, topic, payload, retain=False, qos=0, **kwargs):

        direct = kwargs.get('direct', False)
        properties = kwargs.get('properties', {})

        if not direct:
            topic = "{}/event/{}".format(self.client_topic, topic)
        else:
            topic = "{}".format(topic)

        pub_msg = self.mqtt.Message(topic=topic, payload=payload, retain=retain, qos=qos, **properties)
        await self.mqtt.apub_h(pub_msg)


