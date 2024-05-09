# Copyright (c) 2024 Viktor Vorobjov

from scrivo_telemetry._runner import Telemetry
from scrivo import logging
log = logging.getLogger("tele")


class Runner(Telemetry):

    def activate(self, props):
        log.info("TELEMETRY from COVER")
        self.tele = props
        self.cover = self.core.env("cover")
        self.mbus.sub_h("cmd/cover/#", self.name, "telemetry.reset_act")

    def reset_act(self, msg):
        pld = msg.payload_utf8
        if msg.key == "reset" and pld == "PRESS":
            cover = self.cover.get_cover(msg.topic.split("/")[-1])
            cover.position = 0
            self.notify()

    def reg_config(self):
        cover = self.core.env("cover")
        for key, value in cover._cover.items():
            log.info(f"Reg COVER: {key} -> {value}")

            self.add_config("cover", f"{value.name}",
                            ha_pos_t=f"{self.tele.event_t}/cover/{value.id}/position",
                            ha_cmd_t=f"{self.tele.cmd_t}/cover/{value.id}/set",
                            ha_set_pos_t=f"{self.tele.cmd_t}/cover/{value.id}/set_position",
                            ha_pos_open=0,
                            ha_pos_clsd=value.close_duration,
                            ha_dev_cla="shutter",
                            )
            self.add_config("button", f"{value.name} Reset", ent_cat="config",
                            cmd=f"cover/{value.id}/reset")
            self.add_config("sensor", f"{value.name} Position", ent_cat="config",
                            state=f"cover/{value.id}/position")

    def notify(self):
        cover = self.core.env("cover")
        for key, value in cover._cover.items():
            # log.info(f"COVER: {key} -> {value}")
            self.mbus.pub_h(f"cover/{value.id}/position", value.position)
