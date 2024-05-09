
from scrivo.dev import decode_UTF8
from scrivo.platform import Queue
from scrivo.platform import launch

from scrivo import logging
log = logging.getLogger("MBUS")
# log.setLevel(logging.DEBUG)


class Sub:
    def __init__(self, topic, sub_id, env, func):
        self.topic = topic
        self.sub_id = sub_id
        self.env = env
        self.func = func

    def __str__(self):
        return f"topic: {self.topic}/ sub_id: {self.sub_id} = func: {self.func}"

    def __repr__(self):
        return self.__str__()

    def __call__(self, msg):
        self.func(msg)


class Pub:
    def __init__(self, topic, payload, **properties):
        self.topic = topic
        self.payload = payload
        self.properties = properties
        self.key = None
        self.decode()

    def __str__(self):
        return f"topic: {self.topic} key: {self.key},  payload: {self.payload} = properties: {self.properties}"

    def __repr__(self):
        return self.__str__()

    def decode(self):
        # Split topic, detect for subtopic subscripbe
        pub_topic_split = self.topic.rsplit("/", 1)

        pub_topic = pub_topic_split[0]
        pub_key = pub_topic_split[-1]

        msg_topic = None
        if len(pub_topic_split) > 1:
            msg_topic = pub_topic

        self.pub_topic = pub_topic
        self.topic = msg_topic
        self.key = pub_key

    @property
    def payload_utf8(self):
        try:
            return decode_UTF8(self.payload)
        except Exception as e:
            log.error(f"PAYLOAD_UTF8: {e}")
            return None


class MbusManager:
    def __init__(self, core):
        self.msub = []
        self.queue = Queue(250)
        self.sub_id = 0
        self.core = core
        log.info("START")
        launch(self._publish)

    def path(self, env_name, path):
        # direct use function
        if env_name is None:
            return path

        # use env for define function
        env_call = self.core.env(env_name)
        # log.debug(f"ENV: [{env_name}] => {self.core.env()} -> {env_call}")

        for _attr in path.split("."):
            # log.debug(f"  -> {_attr}")
            if len(_attr):
                env_call = getattr(env_call, _attr)
        return env_call

    # SUB
    def next_sub_id(self):
        self.sub_id += 1
        return self.sub_id

    def sub_h(self, topic, env, func):
        sub_id = self.next_sub_id()
        sub_data = Sub(topic=topic, sub_id=sub_id, env=env, func=func)
        self.msub.append(sub_data)
        return sub_id

    def usub(self, sub_id):
        search_subs = filter(lambda x: x.sub_id == sub_id, self.msub)
        for sub in search_subs:
            self.msub.remove(sub)

    # PUB
    def pub_h(self, topic, payload, **properties):
        pub_data = Pub(topic=topic, payload=payload, **properties)
        self.queue.put_nowait(pub_data)

    async def apub_h(self, topic, payload, **properties):
        pub_data = Pub(topic=topic, payload=payload, **properties)
        await self.queue.put(pub_data)

    # consume messages from queue
    async def _publish(self):
        while True:
            data = await self.queue.get()
            self.event_msg(data)

    async def job(self, method, data):
        await method(data)

    # Event
    def event_msg(self, data):
        # log.debug("      ")
        # log.debug(data)

        # log.debug(f"Topic match pub: {data.pub_topic}")
        for sub in self.msub:
            # log.debug(f"   == {sub.topic}")
            if sub.topic == "/#" or self.topic_match(data.pub_topic, sub.topic):
                # log.debug(f"      -> {sub.func}")
                try:
                    method = self.path(env_name=sub.env, path=sub.func)
                    # log.debug(f"      -> {method}: {data}")
                    launch(method, data)
                except Exception as e:
                    log.error(f"Error: event_msg: {sub.func} - {e}")

    @staticmethod
    def topic_match(target_topic, input_topic):
        target_parts = target_topic.split("/")
        input_parts = input_topic.split("/")
    
        if len(target_parts) > len(input_parts):
            return False
    
        for t, i in zip(target_parts, input_parts):
            if t != i and t != "#" and i != "#":
                return False
    
        return True
