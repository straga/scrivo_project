
try:
    import ujson as json
except ImportError:
    import json


from scrivo.tools.tool import launch

from scrivo import logging
log = logging.getLogger("JSONRPC")


class JsonRpc:

    def __init__(self, core, mbus):
        self.core = core
        self.mbus = mbus

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

    # DB
    async def call_db(self, params, response):

        try:
            # ACTION
            response["result"] = await self.core.uconf.call(
                params["method"],
                params["param"],
                *params["args"],
                **params["kwargs"]
            )
            if self.isgenerator(response["result"]):
                response["result"] = list(response["result"])

        except Exception as e:
            response["error"] = "".format(e)
            log.error("RPC-DB: {}".format(e))
            pass
        return response

    # ENV
    async def call_env(self, params, response):
        try:
            _env = params["env"]
            _path = params["path"]

            # ACTION
            response["result"] = await self.mbus.rpc.action(env_name=_env, path=_path,
                                                            args=params["args"], kwargs=params["kwargs"])
        except Exception as e:
            response["error"] = {"code": 32001, "message": "{}".format(e)}
            log.error("RPC-ENV: {} : {}".format(e, params))
            pass

        return response

    # CALL
    async def call(self, rpc_string):
        response = {
            "id": None,
            "result": None,
            "error" : None
        }

        try:
            jsonrpc = json.loads(rpc_string)
            if "id" in jsonrpc:
                response["id"] = jsonrpc["id"]
            method = jsonrpc["method"]
            parse_params = self.query_params(jsonrpc["params"])
        except Exception as e:
            response["error"] = {"code": 32000, "message": "{}".format(e)}
            log.error("CALL: {}".format(e))
            #log.error("CALL: {} : {}".format(e, rpc_string))
            return json.dumps(response)

        # log.info(parse_params)

        # Method
        call_method = None
        if method == "call_db":
            call_method = self.call_db
        if method == "call_env":
            call_method = self.call_env

        # with response or just call
        if response["id"]:
            response = await call_method(parse_params, response)
            return json.dumps(response)
        else:
            launch(call_method, parse_params, response)