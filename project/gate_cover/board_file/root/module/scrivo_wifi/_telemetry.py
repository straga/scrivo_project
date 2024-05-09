# Copyright (c) 2024 Viktor Vorobjov

from scrivo_telemetry._runner import Telemetry
from scrivo import logging
log = logging.getLogger("tele")


class Runner(Telemetry):
    wifi = None

    def activate(self, props):
        self.wifi = self.core.env("wifi")
        log.info("TELEMETRY from WIFI")

        self.mbus.sub_h("wifi/sta/ip/#", self.name, "telemetry.wifi_act")
        self.mbus.sub_h("cmd/wifi/#", self.name, "telemetry.wifi_cmd")

    def notify(self):
        info = {
            "sta_ip": self.wifi.sta.ifip,
            "hostname": self.wifi.sta.net.config("hostname")
        }
        self.mbus.pub_h("WIFI", info)

    def reg_config(self):
        self.add_config("sensor", "Hostname",   ent_cat="diagnostic", state="WIFI", val_tpl="hostname")
        self.add_config("sensor", "IP",  ent_cat="diagnostic", state="WIFI", val_tpl="sta_ip")
        self.add_config("button", "Wifi Disconect", ent_cat="diagnostic", cmd="wifi/disconnect")

    def wifi_act(self, msg):
        log.info(f"{msg}")

        if msg.payload == "0.0.0.0":
            return
        self.notify()

    def wifi_cmd(self, msg):
        pld = msg.payload_utf8
        if msg.key == "disconnect" and pld == "PRESS":
            self.wifi.sta.net.disconnect()
