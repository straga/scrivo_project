
from scrivo.loader.loader import Load
from .ota import OtaUpdater

from scrivo import logging
log = logging.getLogger("OTA")
# log.setLevel(logging.DEBUG)


class Runner(Load):
    service = None
    push_data = None

    async def _activate(self):
        self.mbus.pub_h("ota_updater", "message")


    def start(self, job, job_stamp, transport):
        #result = "already"
        if not self.service:
            self.service = OtaUpdater()

            # job stamp
            self.service.stamp = job_stamp
            result = {"status": "activate", "stamp": job_stamp}
        else:
            result = {"status": "active", "stamp": self.service.stamp}

        return result


