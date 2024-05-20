
from scrivo.core import Core

from scrivo import logging
log = logging.getLogger("CORE")
#log.setLevel(logging.DEBUG)


class Module:
    def __init__(self, name, env):
        self.name = env
        self.core = Core.core()
        self.mbus = self.core.mbus
        log.info(f"Module init: {name}")

    # Humanize sub to topic
    def sub_h(self, topic, func):
        return self.mbus.sub_h(topic=topic, env=self.name, func=func)

    def activate(self, props):
        pass

    # # use for notify to mbus from other module? need defain what will be send
    def notify(self):
        pass
