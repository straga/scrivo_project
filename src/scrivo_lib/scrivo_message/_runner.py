
from scrivo.loader.loader import Load

from scrivo import logging
log = logging.getLogger("CORE")
# log.setLevel(logging.DEBUG)

class Runner(Load):
    """'
    Just print ALL message form MBUS in console
    """
    brk = []
    sub_id = None

    def echo(self):
        self.sub_id = self.sub_h(topic="/#", func="print_mbus")

    def echo_stop(self):
        if self.sub_id:
            self.mbus.usub(self.sub_id)
            self.sub_id = None

    # async def _activate(self):
    #     self.sub_h(topic="/#", func="print_mbus")
    #
    # @staticmethod
    def print_mbus(self, msg):

        user_property = msg.properties.get("user_property")
        if user_property and "data" in user_property:
            return

        brk = ""
        if msg.properties and "brk" in msg.properties:
            brk = msg.properties['brk']

        if brk in self.brk:
            topic = ""
            if msg.topic:
                topic = "{}/".format(msg.topic)
            log.info(f"MESSAGE: {topic} {msg.key}, {msg.payload} <- {brk}")

        log.debug(f"MESSAGE: {msg.topic} {msg.key}, {msg.payload}  {brk}")


'''
# Work with messages in the relp console.
# Get message object.
from scrivo.core import Core
core = Core.get_core()
message = core.env["message"]

#Makr brk name and run echo. 
message.brk = ["MQTT"]
message.echo()

from scrivo import logging
log = logging.getLogger("CORE")

log.setLevel(logging.DEBUG)
log.setLevel(logging.INFO)
'''
