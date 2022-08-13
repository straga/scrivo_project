
import json

from scrivo import logging
log = logging.getLogger("MQTT")


class Rpc:
    def __init__(self, core, mqtt, mbus):
        self.core = core
        self.mbus = mbus
        self.mqtt = mqtt

    @staticmethod
    def isgenerator(iterable):
        return hasattr(iterable, '__iter__') and not hasattr(iterable, '__len__')


    @staticmethod
    def query_params(params):
        if "args" in params:
            params["args"] = tuple(params["args"])
        else:
            params["args"] = tuple()

        if "kwargs" in params:
            params["kwargs"] = params["kwargs"]
        else:
            params["kwargs"] = dict()

        return params

    async def call(self, topic, payload, properties):
        response = {}

        if "call_db" in properties.user_property:
            # DB
            try:
                _query = json.loads(payload)
                parse_params = self.query_params(_query["params"])

                response["result"] = await self.core.uconf.call(
                    _query["method"],
                    parse_params["param"],
                    *parse_params["args"],
                    **parse_params["kwargs"]
                )

                if self.isgenerator(response["result"]):
                    response["result"] = list(response["result"])

            except Exception as e:
                response["error"] = "".format(e)
                log.error("RPC-DB: {}".format(e))
                pass

        # ENV
        if "call_env" in properties.user_property:
            try:
                # JSON
                _query = json.loads(payload)
                _env = _query["method"]

                param_call = self.query_params(_query["params"])
                param_call_path = param_call["path"]

                # ACTION
                response["result"] = await self.mbus.rpc.action(env_name=_env, path=param_call_path,
                                                                args=param_call["args"], kwargs=param_call["kwargs"])

            except Exception as e:
                response["error"] = "{}".format(e)
                log.error("RPC-ENV: {} : {}".format(e, payload))
                pass

        if hasattr(properties, "response_topic"):
            pub_msg = self.mqtt.Message(topic=properties.response_topic, payload=response)
            self.mqtt.pub(pub_msg)
