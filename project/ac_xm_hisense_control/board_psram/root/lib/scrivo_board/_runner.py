# Copyright (c) 2021 Viktor Vorobjov
import machine
import binascii
from esp32 import Partition
from scrivo.tools.tool import launch, asyncio

from scrivo.loader.loader import Load
from scrivo.u_os import uname, mem_info

from scrivo import logging
log = logging.getLogger("CORE")


class Runner(Load):
    board = None

    async def _activate(self):

        _mod = await self.uconf.call("select_one", "board_cfg", "default", model=True)
        self.board_id = binascii.hexlify(machine.unique_id()).decode()
        log.info("BOARD ID: {}".format(self.board_id))
        self.telemetry_interval = 5
        self.core.action_list.append([self.telemetry, 5, "sec", "BOARD"])
        if _mod:
            # update board_id
            _mod.uid = self.board_id
            await _mod.update()
            #
            self.board = _mod
            self.core.board = self.board

            launch(self.report)

    async def report(self):
        period = 0
        while True:
            for action in self.core.action_list:
                try:
                    if action[2] == "sec":
                        interval = action[1]
                        if period % interval == 0:
                            action[0]()
                    if action[2] == "min":
                        interval = action[1]
                        if period % (60 * interval) == 0:
                            action[0]()

                except Exception as e:
                    log.error(f"TELEMETRY: {e}, {action}")
                await asyncio.sleep(0.01)

            period += 1
            if period > 216000:
                period = 0
            await asyncio.sleep(1)

    def telemetry(self):

        info = {
            "uname": self.uname,
            "mem_info": self.mem_info,
            "part": self.part,
            "datetime": machine.RTC().datetime(),
            "env": list(self.core.env.keys())
        }
        if self.board:
            info["board_id"] = self.board_id,
            info["board"] = self.board.board,
            info["hostname"] = self.board.hostname
        self.mbus.pub_h("BOARD", info)

    @staticmethod
    def reboot(part=None):
        if part:
            _part = Partition(part)
            Partition.set_boot(_part)
        machine.reset()

    @property
    def uname(self):
        return uname()

    # used, free
    @property
    def mem_info(self):
        free, used = mem_info()
        return {"used": used, "free": free}

    @property
    def part(self):
        runningpart = Partition(Partition.RUNNING)
        part_info = runningpart.info()
        part_name = part_info[4]
        return part_name
