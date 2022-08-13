# Copyright (c) 2021 Viktor Vorobjov

import network
import utime
import ntptime

from scrivo.dev import asyncio
from scrivo.dev import launch
from scrivo.core import Core

# from scrivo.thread.thread import run_in_executer

from scrivo import logging
log = logging.getLogger("WIFI")
log.setLevel(logging.DEBUG)


class WIFIRun:

    def __init__(self):

        self.core = Core.get_core()
        log.info("Core")

        self.sta = STA()
        self.scan_ap = self.sta.scan_ap
        log.info("STA")

        self.ap = AP()
        log.info("AP")

        launch(self.keepalive)
        self.core.mbus.pub_h("module", "net")
        log.info("WIFI Task Start")

    # def step(self):
    #     log.info("WIFI Task Start")

    async def keepalive(self):
        sleep = 4
        await self.sta.connect()
        while True:

            if self.sta.net.isconnected() and self.sta.ip != "0.0.0.0":
                sleep = 10
            elif sleep <= 1:
                sleep = 4
                await self.sta.connect()
            else:
                sleep -= 1

            if self.sta.ip == "0.0.0.0" and self.ap.ip == "0.0.0.0":
                launch(self.ap.start)
            elif self.sta.ip and self.ap.ip:
                self.ap.stop()

            # log.info(sleep)
            await asyncio.sleep(sleep)


# Access Point
class AP:
    def __init__(self):
        self.core = Core.get_core()
        self.net = network.WLAN(network.AP_IF)
        self.ip = "0.0.0.0"
        self.ssid = self.net.config("ssid")
        self.delay = 120
        self.stop_progres = False
        launch(self.start)

    async def start(self):

        if self.ip == "0.0.0.0" and not self.stop_progres:
            log.info("AP Active")

            self.net.active(True)
            await asyncio.sleep(0.1)
            # If run active(True) not in thread it block Repl. check in next version esp-idf and upy
            # await run_in_executer(self.net.active, True)

            log.info("AP Select")
            config = await self.core.uconf.call("select", "wifi_ap_cfg", rtype="model", active=True)
            await asyncio.sleep(0.1)

            if config:
                self.ssid = "{}_{}".format(config.ssid, self.core.board.uid)
                log.info(f"AP CONFIG: {config.name} ,  ssid: {self.ssid}")
                try:
                    self.net.config(ssid=self.ssid,
                                    key=config.key,
                                    security=config.security,
                                    channel=config.channel,
                                    hidden=config.hidden)
                    self.delay = config.delay
                except Exception as e:
                    log.error("AP CONFIG: {}".format(e))
                    self.net.active(False)
                    return

        self.ip = self.net.ifconfig()[0]
        log.info("AP IP: {}".format(self.ip))
        self.core.mbus.pub_h("wifi/ap/ip/set", self.ip)

    async def _stop(self):
        self.stop_progres = True
        await asyncio.sleep(self.delay)
        self.ip = "0.0.0.0"
        self.net.active(False)
        self.core.mbus.pub_h("wifi/ap/ip/set", None)
        self.stop_progres = False

    def stop(self):
        if not self.stop_progres and self.delay > 0:
            launch(self._stop)


# Connect to AP
class STA:

    def __init__(self):

        self.core = Core.get_core()
        self.mbus = self.core.mbus
        self.uconf = self.core.uconf
        self.progress = False
        log.info("STA Core")

        self.net = network.WLAN(network.STA_IF)
        log.info("STA Net")

        self.net.active(True)

        log.info("STA ps_mode: WIFI_PS_NONE")
        try:
            # WIFI_PS_NONE = 0, for espnow
            # WIFI_PS_MAX_MODEM = 1
            # WIFI_PS_MAX_MODEM = 2
            self.net.config(ps_mode=network.WIFI_PS_NONE)
        except Exception as e:
            log.error(f"sta ps_mode: {e}")

        log.info("STA Active")
        try:
            self.net.config(dhcp_hostname=self.core.board.hostname)
        except Exception as e:
            log.error(f"dhcp_hostname: {e}")

        try:
            self.net.config(hostname=self.core.board.hostname)
        except Exception as e:
            log.error(f"hostname: {e}")

        self.ip = "0.0.0.0"
        self.channel = -1
        log.info("STA Config")
        self.status_echo()


    def status_echo(self):
        ip = self.net.ifconfig()[0]
        self.channel = self.net.config("channel")
        log.info(f"STA: IP: {ip} channel: {self.channel}")
        if ip != self.ip:
            self.ip = ip
            self.mbus.pub_h("wifi/sta/ip/set", self.ip)
            try:
                ntptime.settime()
                log.info(f"Get time: {utime.localtime()}")
            except Exception as e:
                log.error(f"Get time: {e}")
                pass


    async def connect(self):

        if not self.net.isconnected():
            sta_configs = await self.uconf.call("scan_name", "wifi_sta_cfg")
            await asyncio.sleep(0.1)

            if sta_configs:

                log.debug("Disconect")
                self.net.disconnect()

                self.ip = "0.0.0.0"
                self.mbus.pub_h("wifi/sta/ip/set", self.ip)
                log.debug("STA: configs =  {}".format(sta_configs))
                ap_names = self.scan_ap(only_name=True)
                log.debug("STA: scan: {}".format(ap_names))

                for config in sta_configs:
                    ap_conf = await self.uconf.call("select_one", "wifi_sta_cfg", config, False)
                    await asyncio.sleep(0.1)

                    try:
                        if "protocol" in ap_conf and ap_conf["protocol"] != -1:
                            log.info("STA: protocol mode for espnow activated")
                            self.net.config(protocol=ap_conf["protocol"])
                    except Exception as e:
                        log.error(f"sta protocol: {e}")

                    # log.info("STA ps_mode: from config")
                    # try:
                    #     if "espnow" in ap_conf and ap_conf["espnow"]:
                    #         log.info("STA: power mode for espnow activated")
                    #         if self.net.config("ps_mode") != network.WIFI_PS_NONE:
                    #             self.net.config(ps_mode=network.WIFI_PS_NONE)
                    #     else:
                    #         log.info("STA: power mode default")
                    #         self.net.config(ps_mode=1)
                    # except Exception as e:
                    #     log.error(f"sta ps_mode: {e}")

                    log.debug("STA: try connect to SSID =  {}".format(ap_conf["ssid"]))
                    if ap_conf["ssid"] in ap_names:
                        log.debug("STA: key len =  {}".format(len(ap_conf["key"])))
                        self.net.connect(ap_conf["ssid"], ap_conf["key"])
                        log.info("STA: connect to: {}".format(ap_conf["ssid"]))
                        await asyncio.sleep(15)
                        result = self.net.isconnected()
                        log.info("STA: connected: {}".format(result))
                        if result:
                            self.status_echo()
                            break




    def scan_ap(self, only_name=False):
        data = []
        if only_name:
            try:
                for ap in self.net.scan():
                    data.append(ap[0].decode())
            except Exception as e:
                log.error("scan: {}".format(e))
                pass
        else:
            try:
                for ap in self.net.scan():
                    val = {
                        "ssid": ap[0].decode(),
                        "bssid": "",
                        "channel": ap[2],
                        "RSSI": ap[3],
                        "security": ap[4],
                        "hidden": ap[5]
                        }
                    data.append(val)
            except Exception as e:
                log.error("scan: {}".format(e))
                pass
        return data


