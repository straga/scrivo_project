# Copyright (c) 2021 Viktor Vorobjov

from scrivo.tools.tool import launch
from scrivo.tools.tool import DataClassArg
from .rpcenv import RpcEnv

from scrivo import logging
log = logging.getLogger("MBUS")


class MbusManager:
    def __init__(self):
        self.msub = []
        self.sub_id = 0
        self.rpc = None


    def activate(self, core):
        self.rpc = RpcEnv(core)

    # SUB
    def next_sub_id(self):
        self.sub_id += 1
        return self.sub_id

    @staticmethod
    def proto_subs(topic, sub_id, env, func):
        proto = DataClassArg(topic=topic, sub_id=sub_id, env=env, func=func)
        return proto

    def sub_h(self, topic, env, func):
        sub_id = self.next_sub_id()
        sub_data = self.proto_subs(topic=topic, sub_id=sub_id, env=env, func=func)
        self.msub.append(sub_data)
        return sub_id

    def usub(self, sub_id):
        search_subs = filter(lambda x: x.sub_id == sub_id, self.msub)
        for sub in search_subs:
            self.msub.remove(sub)

    # PUB
    @staticmethod
    def proto_msg(topic, payload, **properties):
        return DataClassArg(topic=topic, payload=payload, properties=properties)


    def pub_h(self, topic, payload, **properties):
        pub_data = self.proto_msg(topic=topic, payload=payload, **properties)
        self.event_msg(pub_data)


    # Event
    def event_msg(self, data):

        # log.debug("      ")
        # log.debug("[PUB MSG]: tpc: {}, pld:{}".format(data.topic, data.payload))

        # Split topic, detect for subtopic subscripbe
        pub_topic_split = data.topic.rsplit("/", 1)

        pub_topic = pub_topic_split[0]
        pub_key = pub_topic_split[-1]
        # log.debug("Pub: {}, key: {}".format(pub_topic, pub_key))

        msg_topic = None
        if len(pub_topic_split) > 1:
            msg_topic = pub_topic

        for sub in list(filter(lambda x: x.topic.rsplit("/#", 1)[0] in pub_topic, self.msub)):

            # log.debug("  sub Env: {}".format(sub.env))

            data.topic = msg_topic
            data.key = pub_key
            # log.info(f"PUB: {data.__dict__}")
            try:
                method = self.rpc.path(env_name=sub.env, path=sub.func)
                launch(method, data)
            except Exception as e:
                log.error(f"  Error: call_back: {sub.func} - {e}")
                pass
