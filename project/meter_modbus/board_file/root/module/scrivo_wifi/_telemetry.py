# Copyright (c) 2024 Viktor Vorobjov
from scrivo.platform import launch
from scrivo_telemetry._runner import Telemetry
from scrivo import logging
log = logging.getLogger("tele")


class Runner(Telemetry):
    wifi = None
    run_notify = False

    def activate(self, props):
        log.info("TELEMETRY from WIFI")
        self.wifi = self.core.env("wifi")
        self.mbus.sub_h("cmd/wifi/#", self.name, "telemetry.wifi_disconnect")
        self.mbus.sub_h("wifi/sta/ip/#", self.name, "telemetry.pub_notify")

    async def reg_config(self):
        await self.add_config("sensor", "Hostname",   ent_cat="diagnostic", state="WIFI", val_tpl="hostname")
        await self.add_config("sensor", "IP",  ent_cat="diagnostic", state="WIFI", val_tpl="sta_ip")
        await self.add_config("button", "Wifi Disconect", ent_cat="diagnostic", cmd="wifi/disconnect")

    def wifi_disconnect(self, msg):
        pld = msg.payload_utf8
        if msg.key == "disconnect" and pld == "PRESS":
            self.wifi.sta.net.disconnect()


    def pub_notify(self, msg):
        if self.run_notify:
            return
        launch(self.notify)


    async def notify(self):
        self.run_notify = True
        info = {
            "sta_ip": self.wifi.sta.ifip,
            "hostname": self.wifi.sta.net.config("hostname")
        }
        await self.apub("WIFI", info)
        self.run_notify = False

