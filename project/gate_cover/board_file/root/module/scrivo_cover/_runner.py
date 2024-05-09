# Copyright (c) 2021 Viktor Vorobjov

import asyncio
from scrivo.module import Module
from scrivo.dev import DataClassArg
import time

from scrivo import logging
log = logging.getLogger("COVER")
# log.setLevel(logging.DEBUG)


class Config(DataClassArg):
    id = "Home"
    name = "Cover"
    relay_1 = "r1"
    relay_2 = "r2"
    close_duration = 100
    status = "status"
    position = 0
    move_start_time = None  # new attribute to store the move start time


class Runner(Module):
    _cover = {}
    progress = False
    progress_time = 0

    def activate(self, props):
        log.debug(f"Activate: {props}")
        self.mbus.sub_h("cmd/cover/#", self.name, "cover_control")
        switch_env = self.core.env("switch")

        for config in props.configs:
            log.info(f"Add Config params to module: {config}")
            config = Config.from_dict(config)

            config.relay_1 = switch_env.get_switch(config.relay_1)
            config.relay_2 = switch_env.get_switch(config.relay_2)

            self._cover[config.id] = config

    def get_cover(self, cover_id=None):
        cover = self._cover.get(cover_id, None)
        return cover

    async def open_wait(self, cover, duration=None):
        totaly = False
        if duration is None:
            duration = 0
            totaly = True
        self.progress = True
        cover.relay_1.change_state(1)
        while self.progress:
            await asyncio.sleep(1)
            cover.position -= 1
            if cover.position < 0:
                cover.position = 0
            self.mbus.pub_h(f"cover/{cover.id}/position", cover.position)
            if cover.position == duration:
                if totaly:
                    for _ in range(15):  # add an additional delay
                        if not self.progress:  # check if the "STOP" command was received
                            break
                        await asyncio.sleep(1)
                self.progress = False
        cover.relay_1.change_state(0)

    async def close_wait(self, cover, duration=None):
        totaly = False
        if duration is None:
            duration = cover.close_duration
            totaly = True
        self.progress = True

        cover.relay_2.change_state(1)
        while self.progress:
            await asyncio.sleep(1)
            cover.position += 1
            self.mbus.pub_h(f"cover/{cover.id}/position", cover.position)
            if cover.position >= duration:
                if totaly:
                    for _ in range(15):  # add an additional delay
                        if not self.progress:  # check if the "STOP" command was received
                            break
                        await asyncio.sleep(1)
                self.progress = False
        cover.relay_2.change_state(0)

    async def cover_control(self, msg):
        log.debug(f"Cover Ctrl: {msg}")

        cover = self.get_cover(msg.topic.split("/")[-1])
        if cover:
            if msg.key == "set_position":
                payload = msg.payload_utf8
                position = int(payload)

                if position > cover.position and not self.progress:
                    await self.close_wait(cover, position)

                elif position < cover.position and not self.progress:
                    await self.open_wait(cover, position)

            if msg.key == "set":
                payload = msg.payload_utf8 #payload in ["OPEN", "CLOSE", "STOP"]:

                if payload == "OPEN" and not self.progress:
                    cover.status = "OPEN"
                    cover.move_start_time = time.time()  # save the current time
                    await self.open_wait(cover)

                elif payload == "CLOSE" and not self.progress:
                    cover.status = "CLOSE"
                    cover.move_start_time = time.time()  # save the current time
                    await self.close_wait(cover)

                elif payload == "STOP":
                    self.progress = False
                    cover.relay_1.change_state(0)
                    cover.relay_2.change_state(0)
                    cover.status = "STOP"
                    position = cover.position
                    elapsed_time = time.time() - cover.move_start_time  # calculate the elapsed time
                    position += elapsed_time  # update the position
                    if position > cover.close_duration:
                        cover.position = cover.close_duration
                        self.mbus.pub_h(f"cover/{cover.id}/position", cover.position)
