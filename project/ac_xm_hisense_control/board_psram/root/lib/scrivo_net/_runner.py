# Copyright (c) 2021 Viktor Vorobjov

from scrivo.loader.loader import Load
from scrivo.dev import asyncio
from .wifi import WIFIRun

from scrivo import logging
log = logging.getLogger("NET")


class Runner(Load):

    async def _activate(self):
        self.wifi = WIFIRun()
        self.core.action_list.append([self.telemetry, 5, "sec", "NET"])

    def telemetry(self):
        info = {
            "sta_ip": self.wifi.sta.ip,
            "ap_ssid": self.wifi.ap.ssid,
            "ap_ip": self.wifi.ap.ip
        }
        self.mbus.pub_h("NET", info)




