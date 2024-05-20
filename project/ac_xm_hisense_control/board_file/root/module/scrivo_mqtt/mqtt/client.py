# Copyright (c) 2020 Viktor Vorobjov

import asyncio
from scrivo.platform import Queue
from scrivo.dev import DataClassArg
from scrivo.platform import launch

from .package import MQTTPacket
from .connection import MQTTConnect
from .message import Message, Subscription

from scrivo import logging
log = logging.getLogger("MQTT")

import micropython

class MQTTClient:
    class Message(Message):
        pass

    class Subscription(Subscription):
        pass

    def __init__(self, client_id, addr, port, clean=True, keepalive=10, maxsize=None):

        self.client_id = client_id
        self.connect = MQTTConnect(self, addr, port)
        self.protocol = DataClassArg(name=b'MQTT', ver=5)  # MQTTv311 = 4, # MQTTv5 = 5

        self.birth = None

        self.on_message = None
        self.pid = 0
        self.fail = 0
        self._run = False

        self.keepalive = keepalive
        self.ping_interval = 0.5 * keepalive

        self.open_status = 0
        self.broker_status = 0

        self.clean = clean
        self.username = None
        self.password = None
        self.will_message = None

        self.sleep = 1
        self.lock = asyncio.Lock()

        self.queue = Queue()
        if maxsize is not None:
            self.queue = Queue(maxsize)

        launch(self.mqtt_publish)

    # consume messages from queue
    async def mqtt_publish(self):
        while True:
            data = await self.queue.get()

            #log.info(f"[PUB] {data.topic}")
            #log.info(micropython.mem_info())

            await self.task_publish(data)



    async def connect_action(self):
        packet = MQTTPacket.login(client_id=self.client_id,
                                  username=self.username,
                                  password=self.password,
                                  clean_session=self.clean,
                                  keepalive=self.keepalive,
                                  will_message=self.will_message,
                                  protocol=self.protocol)
        await self.connect.transport.awrite(packet, True)

    def on_connect(self, client):
        pass

    def on_disconnect(self, client):
        pass

    def on_subscribe(self, client):
        pass

    def on_puback(self, client):
        pass

    def on_message_task(self, client, **kwargs):
        if self.on_message:
            launch(self.on_message, client=client, **kwargs)

    # PID
    def newpid(self):
        return self.pid + 1 if self.pid < 65535 else 1

    # SUB
    def subscribe(self, sbt):
        for sb in sbt:
            log.info(f"[SUB Topic] : {sb.topic}")
        packet = MQTTPacket.subscribe(sbt=sbt, protocol=self.protocol, mid=self.newpid())
        launch(self.connect.transport.awrite, packet, True)

    # PUB
    def pub(self, data=None, *args, **kwargs):
        if data is None:
            data = self.Message(*args, **kwargs)
        self.queue.put_nowait(data)

    async def apub_h(self, data=None, *args, **kwargs):
        if data is None:
            data = self.Message(*args, **kwargs)
        await self.queue.put(data)

    async def task_publish(self, data):
        if self.broker_status:
            packet = MQTTPacket.publish(data, self.newpid(), self.protocol)
            await self.connect.transport.awrite(packet, True)
    # # PUB
    # def pub(self, data=None, *args, loop=None, **kwargs):
    #     if data is None:
    #         data = self.Message(*args, **kwargs)
    #     launch(self.task_publish, data, loop=loop)
    #
    # async def task_publish(self, data):
    #     if self.broker_status:
    #         packet = MQTTPacket.publish(data, self.newpid(), self.protocol)
    #         await self.connect.transport.awrite(packet, True)

    # Ping

    async def mqtt_keepalive(self):
        while self._run:
            if self.broker_status:
                await self.ping()
            if self.open_status == 0:
                await self.reconnect()
            await asyncio.sleep(1)

    async def ping(self):
        try:
            packet = MQTTPacket.ping()
            await self.connect.transport.awrite(packet, True)
            log.debug(f"[fail] {self.fail}")
            self.fail += 1
            if self.fail > 3:
                self.fail = 0
                await self.connect.close("ping")
            await asyncio.sleep(self.ping_interval)
        except Exception as e:
            log.error(f"Error in ping: {e}")

    async def reconnect(self):
        try:
            self.sleep += 1
            if self.sleep > 60:
                self.sleep = 1
            await asyncio.sleep(self.sleep)
            await self.connect.create_connect()
            log.debug("[CONNECT] to MQTT")
        except Exception as e:
            log.error(f"Error in reconnect: {e}")


    # async def mqtt_keepalive(self):
    #     period = 0
    #
    #     while self._run:
    #         # log.info(f"[FAIL] {self.fail}, con status: {self.broker_status}, open status: {self.open_status}")
    #         # PING
    #
    #         if period % self.ping_interval == 0:
    #             log.debug(f"[PING] {period}, {self.ping_interval}, {self.fail}")
    #
    #             if self.broker_status:
    #                 packet = MQTTPacket.ping()
    #                 await self.connect.transport.awrite(packet, True)
    #
    #             if self.fail > 3:
    #                 self.fail = 0
    #                 await self.connect.close("ping")
    #
    #             self.fail += 1
    #
    #
    #         # RE-CONNECT
    #         if self.open_status == 0:
    #
    #             await asyncio.sleep(self.sleep)
    #
    #             self.sleep += 1
    #             if self.sleep > 60:
    #                 self.sleep = 1
    #
    #             await self.connect.create_connect()
    #             log.debug("[CONNECT] to MQTT")
    #
    #         period += 1
    #         if period > 3600:
    #             period = 0
    #         await asyncio.sleep(1)



    def start(self):
        if not self._run:
            log.info(f"[CONNECT] Start = {self.connect.addr}:{self.connect.port}")
            self._run = True
            # launch(self.mqtt_connect)
            # launch(self.mqtt_ping)
            launch(self.mqtt_keepalive)

    def stop(self):
        self._run = False
        launch(self.connect.close)








