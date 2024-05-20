# Copyright (c) 2024 Viktor Vorobjov

import asyncio
from scrivo_telemetry._runner import Telemetry
from scrivo.platform import launch
from scrivo.dev import decode_payload
from scrivo import logging
log = logging.getLogger("tele")

from .responses import _Data_101_0, _Data_102_64, _Data_102_0, _Data_7_1, _Data_10_4, _Data_30_0

class Runner(Telemetry):

    def activate(self, props):

        log.info("TELEMETRY from AC")
        self.tele = props
        self.ac = self.core.env("acxm")

        self.mbus.sub_h("cmd/ac_control/#", self.name, "telemetry.ac_act")
        self.core.cron("AC info", self.ac_info, 15, "sec")

        self.blacklist = ["rev23", "rev25", "rev47", "rev48", "rev49", "rev50", "rev51", "rev52", "rev53", "rev54", "rev55", "rev56"]

        launch(self.ac_event)


    async def notify(self):
        # Clear all data
        # AC status
        for data in _Data_102_0:
            data["val"] = None
        await asyncio.sleep(0.01)


    async def reg_config(self):
        await self.add_config("sensor", "AC ping", ent_cat="diagnostic", state="BOARD/ac_ping")

        for idx, _data in enumerate(_Data_102_0):
            name = _data["name"]
            if name not in self.blacklist:
                await self.add_config("sensor", f"AC {name}", state=f"status/{name}")

        for idx, _data in enumerate(_Data_102_64):
            name = _data["name"]
            await self.add_config("sensor", f"KWH {name}", state=f"kwh/{name}")

        for idx, _data in enumerate(_Data_7_1):
            name = _data["name"]
            await self.add_config("sensor", f"Soft {name}", state=f"soft/{name}")

        for idx, _data in enumerate(_Data_10_4):
            name = _data["name"]
            await self.add_config("sensor", f"Recv {name}", state=f"recv/{name}")

        for idx, _data in enumerate(_Data_30_0):
            name = _data["name"]
            await self.add_config("sensor", f"Ping {name}", state=f"ping/{name}")



        # SWITCH
        await self.add_config("switch", "Run Status",
                        state=f"status/run_status", cmd="ac_control/run_status", ic="mdi:power",
                        ha_pl_off="off", ha_pl_on="on")

        await self.add_config("switch", "Low Electricity",
                        state=f"status/low_electricity", cmd="ac_control/low_electricity", ic="mdi:power-plug",
                        ha_pl_off="off", ha_pl_on="on")

        await self.add_config("switch", "Up Down",
                        state=f"status/up_down", cmd="ac_control/up_down", ic="mdi:arrow-up-down",
                        ha_pl_off="off", ha_pl_on="on")

        await self.add_config("switch", "Left Right",
                        state=f"status/left_right", cmd="ac_control/left_right", ic="mdi:arrow-left-right",
                        ha_pl_off="off", ha_pl_on="on")

        await self.add_config("switch", "Turbo",
                        state=f"status/efficient", cmd="ac_control/turbo", ic="mdi:fan",
                        ha_pl_off="off", ha_pl_on="on")

        await self.add_config("switch", "Mute",
                        state=f"status/mute", cmd="ac_control/quiet", ic="mdi:volume-mute",
                        ha_pl_off="off", ha_pl_on="on")

        await self.add_config("switch", "Back LED",
                        state=f"status/back_led", cmd="ac_control/back_led", ic="mdi:led-strip",
                        ha_pl_off="off", ha_pl_on="on")

        # SELECT
        await self.add_config("select", "Wind Status",
                        state=f"status/wind_status", cmd="ac_control/wind_status", ic="mdi:fan",
                        ha_ops=["off", "auto", "lower", "low", "medium", "high", "higher"])

        await self.add_config("select", "Sleep Status",
                        state=f"status/sleep_status", cmd="ac_control/sleep_status", ic="mdi:sleep",
                        ha_ops=["off","0", "1", "2", "3", "4"])

        await self.add_config("select", "Mode Status",
                        state=f"status/mode_status", cmd="ac_control/mode_status", ic="mdi:air-conditioner",
                        ha_ops=["cool", "fan_only", "heat", "dry", "auto"])

        # NUMBER SLIDER
        await self.add_config("number", "Temp Indoor Set", ha_mode="slider",
                        state=f"status/indoor_temperature_setting", cmd="ac_control/temp_in", ic="mdi:thermometer",
                        ha_min=16, ha_max=30, ha_step=1, ha_sleep_status="°C")

    async def ac_event(self):
        while True:
            if self.ac.event:
                await self.ac.event.wait()
                await self.ac_data()
                self.ac.event.clear()
            await asyncio.sleep(0.01)

    async def ac_data(self):
        if self.tele._alive:
            # Ping
            await self.tele.mqtt.apub_msg("BOARD/ac_ping", self.ac.ac_ping)

            # AC status
            for idx, data in enumerate(_Data_102_0):
                new_data = self.ac.store_102[idx]
                if new_data is not None and "val" in data:
                    if new_data != data["val"]:
                        name = data["name"]
                        log.info(f"AC: {data["val"]} -> {new_data} : {name}")
                        data["val"] = new_data
                        if name not in self.blacklist:
                            await self.tele.mqtt.apub_msg(f"status/{name}", new_data)
        await asyncio.sleep(0.01)

    async def ac_info(self):
        if self.tele._alive:
            for idx, data in enumerate(_Data_102_64):
                data["val"] = self.ac.store_102_64[idx]
                if data["val"] is not None:
                    name = data["name"]
                    await self.tele.mqtt.apub_msg(f"kwh/{name}", data["val"])
                await asyncio.sleep(0.01)

            for idx, data in enumerate(_Data_7_1):
                data["val"] = self.ac.store_7_1[idx]
                if data["val"] is not None:
                    name = data["name"]
                    await self.tele.mqtt.apub_msg(f"soft/{name}", data["val"])
                await asyncio.sleep(0.01)

            for idx, data in enumerate(_Data_10_4):
                data["val"] = self.ac.store_10_4[idx]
                if data["val"] is not None:
                    name = data["name"]
                    await self.tele.mqtt.apub_msg(f"recv/{name}", data["val"])
                await asyncio.sleep(0.01)

            for idx, data in enumerate(_Data_30_0):
                data["val"] = self.ac.store_30_0[idx]
                if data["val"] is not None:
                    name = data["name"]
                    await self.tele.mqtt.apub_msg(f"ping/{name}", data["val"])
                await asyncio.sleep(0.01)

        await asyncio.sleep(0.01)


    @decode_payload
    async def ac_act(self, msg):
        log.info("")
        log.info(f"ac_control: t: {msg.topic},  k: {msg.key}, p: {msg.payload}")

        msg.payload = msg.payload.lower()
        async with self.ac.lock:
            if msg.key == "run_status":
                await self.ac.cmd("101_0", {"run_status": msg.payload})

            elif msg.key == "temp_fahrenheit":
                await self.ac.cmd("101_0", {"temp_fahrenheit": msg.payload})

            elif msg.key == "up_down":
                await self.ac.cmd("101_0", {"up_down": msg.payload})

            elif msg.key == "left_right":
                await self.ac.cmd("101_0", {"left_right": msg.payload})

            elif msg.key == "low_electricity":
                if msg.payload == "on":
                    await self.ac.cmd("101_0", {"low_electricity": "on", "wind_status": "lower"})
                elif msg.payload == "off":
                    await self.ac.cmd("101_0", {"low_electricity": "off"})

            elif msg.key == "turbo":
                await self.ac.cmd("101_0", {"turbo": msg.payload})

            elif msg.key == "quiet":
                if msg.payload == "on":
                    await self.ac.cmd("101_0", {"mute": "on", "wind_status": "lower"})
                elif msg.payload == "off":
                    await self.ac.cmd("101_0", {"mute": "off"})

            elif msg.key == "back_led":
                await self.ac.cmd("101_0", {"back_led": msg.payload})

            elif msg.key == "temp_in":
                temperature = int(msg.payload.split('.')[0])
                await self.ac.cmd("101_0", {"temp_indoor_set": temperature})

            elif msg.key == "mode_status":
                await self.ac.cmd("101_0", {"mode_status": msg.payload})

            elif msg.key == "wind_status":
                await self.ac.cmd("101_0", {"wind_status": msg.payload})

            elif msg.key == "swing":
                if msg.payload == "both":
                    await self.ac.cmd("101_0", {"left_right": "on", "up_down": "on"})
                elif msg.payload == "vertical":
                    await self.ac.cmd("101_0", {"left_right": "off", "up_down": "on"})
                elif msg.payload == "horizontal":
                    await self.ac.cmd("101_0", {"left_right": "on", "up_down": "off"})
                elif msg.payload == "off":
                    await self.ac.cmd("101_0", {"left_right": "off", "up_down": "off"})

