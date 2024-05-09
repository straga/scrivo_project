# Copyright (c) 2023 Viktor Vorobjov

import network
import asyncio
from scrivo.core import Core

from scrivo import logging
log = logging.getLogger("WIFI")

MIN_KEY_LENGTH = 7
SLEEP_TIME = 1
LONG_SLEEP_TIME = 15
IP_DEFAULT = "0.0.0.0"


def find_strongest_network(sta, target_key):
    strongest_signal = None
    strongest_strength = float("-inf")

    for sta_device in sta:
        try:
            log.info("scan: {}".format(sta_device))
            ssid, _, _, signal_strength, _, _ = sta_device
            if ssid.decode() == target_key and signal_strength > strongest_strength:
                strongest_signal = sta_device
                strongest_strength = signal_strength
        except Exception as e:
            log.error("scan: {}".format(e))
            pass
    return strongest_signal


class STA:

    def __init__(self, networks):
        log.info("STA Init")
        self.ip = IP_DEFAULT
        self.try_connect = 0
        self.core = Core.core()
        self.networks = networks
        self.mbus = self.core.mbus
        self.net = network.WLAN(network.STA_IF)
        self.net.active(True)
        log.info("STA Activate Network")

    @property
    def ifip(self):
        return self.net.ifconfig()[0]


    @property
    def isconnected(self):
        return self.net.isconnected()

    async def sta_connect(self):
        if self.try_connect == 1:
            await asyncio.sleep(0.1)
            return

        self.try_connect = 1
        if not self.isconnected:
            await self.disconnect_and_reactivate()
            sta_scan = await self.scan_networks()
            await self.connect_to_network(sta_scan)

        self.update_state()
        self.try_connect = 0
        await asyncio.sleep(0.1)

    async def disconnect_and_reactivate(self):
        log.debug("Disconnecting...")
        self.net.disconnect()
        await asyncio.sleep(1)
        self.mbus.pub_h("wifi/sta/ip/set", self.ip)
        self.net.active(False)
        await asyncio.sleep(1)
        self.net.active(True)

    async def scan_networks(self):
        try:
            return self.net.scan()
        except Exception as e:
            log.error(f"Failed to scan networks: {e}")
            return []

    async def connect_to_network(self, sta_scan):
        for config in self.networks:
            _ssid = config.get("ssid")
            _password = config.get("password")

            if _ssid and _password and len(_password) > MIN_KEY_LENGTH:
                sta = find_strongest_network(sta_scan, _ssid)

                if sta:
                    await self.connect_to_ssid(_ssid, _password, sta[1])
                    if self.isconnected:
                        break
                else:
                    log.debug("STA: network not found")
                    await asyncio.sleep(SLEEP_TIME)
            else:
                log.debug(f"STA: config not found - len= {_password}")
                await asyncio.sleep(SLEEP_TIME)

    async def connect_to_ssid(self, ssid, password, bssid):
        self.net.connect(ssid, password, bssid=bssid)
        log.info(f"STA: connect to: {ssid} key: {password}, bssid: {bssid}")
        await asyncio.sleep(LONG_SLEEP_TIME)
        log.info(f"STA: connected: {self.isconnected}")

    def update_state(self):
        ip = self.net.ifconfig()[0] if self.isconnected else IP_DEFAULT
        if ip != self.ip:
            self.ip = ip
            self.mbus.pub_h("wifi/sta/ip/set", self.ip)


