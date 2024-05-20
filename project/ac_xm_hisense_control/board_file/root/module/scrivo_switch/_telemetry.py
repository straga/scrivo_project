# Copyright (c) Viktor Vorobjov

from scrivo_telemetry._runner import Telemetry
from scrivo import logging
log = logging.getLogger("tele")

class Runner(Telemetry):

    def activate(self, props):
        log.info("TELEMETRY from SWITCH")
        self.sw_env = self.core.env("switch")

    async def notify(self):
        for sw in self.sw_env._switches.values():
            await self.apub(sw.stat_t, self.sw_env.get_state(sw), retain=True)

    async def reg_config(self):

        for sw in self.sw_env._switches.values():
            log.info(f"SWITCH: {sw}")
            ic = "mdi:toggle-switch"
            if hasattr(sw, "ic"):
                ic = sw.ic

            if sw.mode == "switch" or sw.mode is None:
                await self.add_config("switch", sw.name, state=sw.stat_t, cmd=f"switch/{sw.id}/set", ic=ic)
            elif sw.mode == "button":
                await self.add_config("button", sw.name, cmd=f"switch/{sw.id}/set", ic=ic)
                await self.add_config("sensor", sw.name, state=sw.stat_t, ic=ic)

