# Copyright (c) 2024 Viktor Vorobjov

import os
import gc
import machine
from esp32 import Partition

from scrivo_telemetry._runner import Telemetry
from scrivo import logging
log = logging.getLogger("tele")


class Runner(Telemetry):

    def activate(self, props):
        self.board = self.core.env("board")
        log.info("TELEMETRY from BOARD")

        self.mbus.sub_h("cmd/button/board/#", self.name, "telemetry.button_act")
        self.core.cron("BOARD", self.mem_tele, 15, "sec")

    def notify(self):
        info = {
            "name": self.board.name,
            "part": self.part,
            "board_id": self.board.board_id,
            "frw": self.uname,
        }
        self.mbus.pub_h("Board/info", info)

    def reg_config(self):
        ent_cat = "diagnostic"
        self.add_config("sensor", "Name",  ent_cat=ent_cat, state="Board/info", val_tpl="name")
        self.add_config("sensor", "Partition", ent_cat=ent_cat, state="Board/info", val_tpl="part")
        self.add_config("sensor", "ID", ent_cat=ent_cat, state="Board/info", val_tpl="board_id")
        self.add_config("sensor", "firmware", ent_cat=ent_cat, state="Board/info", val_tpl="frw")
        self.add_config("sensor", "mem free", ent_cat=ent_cat, state="BOARD/mem", val_tpl="free")
        self.add_config("sensor", "mem used", ent_cat=ent_cat, state="BOARD/mem", val_tpl="used")

        self.add_config("button", "Board reboot", ent_cat=ent_cat, cmd="button/board/reboot")

    @staticmethod
    def reboot(part=None):
        if part:
            _part = Partition(part)
            Partition.set_boot(_part)
        machine.reset()

    def button_act(self, msg):
        #log.info(msg)
        pld = msg.payload_utf8
        #log.info(f"PUSH: pld: {pld}")

        if msg.key == "reboot" and pld == "PRESS":
            self.reboot()

    async def mem_tele(self):
        await self.mbus.apub_h("BOARD/mem", self.mem_info)

    @property
    def mem_info(self):
        return {"used": gc.mem_alloc(), "free": gc.mem_free()}

    @property
    def uname(self):
        return list(os.uname())

    @property
    def part(self):
        runningpart = Partition(Partition.RUNNING)
        part_info = runningpart.info()
        part_name = part_info[4]
        return part_name

