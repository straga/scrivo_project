# Copyright (c) 2024 Viktor Vorobjov
import asyncio
from scrivo.module import Module
from scrivo.platform import launch

import ntptime
import time

from scrivo import logging
log = logging.getLogger("WIFI")
#log.setLevel(logging.DEBUG)


class Runner(Module):

    sta = None
    ap = None
    safe = ["ftp", "telnet"]

    def activate(self, props):
        log.debug(f"Activate: {props}")

        if props.sub == "runner":
            for config in props.configs:
                if config.get("safe") is not None:
                    self.safe = config["safe"]

        if props.sub == "networks":
            from .sta import STA
            self.sta = STA(props.configs)
            self.mbus.sub_h("wifi/sta/ip/#", self.name, "wifi_act")
            launch(self.wifi_keepalive)

        if props.sub == "ap":
            for config in props.configs:
                log.info(f"Add Config params to module: {config}")

    async def wifi_keepalive(self):
        log.info("Keepalive")
        while True:
            try:
                await self.sta.sta_connect()
            except Exception as e:
                log.error(f"Keepalive: {e}")
            await asyncio.sleep(5)

    def safe_mode(self):
        log.info("Safe mode: {}".format(self.safe))
        if self.safe:
            if "ftp" in self.safe:
                try:
                    import uftpd
                    uftpd.stop()
                    uftpd.start()
                except Exception as e:
                    log.error(f"FTP: {e}")

            if "telnet" in self.safe:
                try:
                    import utelnetserver
                    utelnetserver.stop()
                    utelnetserver.start()
                except Exception as e:
                    log.error(f"Telnet: {e}")


    def wifi_act(self, msg):
        log.info(f"{msg}")

        # not update if not get IP
        if msg.payload == "0.0.0.0":
            return

        # update datetime from ntp
        try:
            ntptime.settime()
            log.info(f"Get time: {time.localtime()}")
        except Exception as e:
            log.error(f"Get time: {e}")

        # If activate safa mode, restart ftp and telnet
        self.safe_mode()


