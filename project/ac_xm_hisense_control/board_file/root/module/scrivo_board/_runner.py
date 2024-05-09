# Copyright (c) 2024 Viktor Vorobjov
import machine
import binascii

from scrivo.module import Module

from scrivo import logging
log = logging.getLogger("BOARD")


class Runner(Module):
    board_id = binascii.hexlify(machine.unique_id()).decode()

    def activate(self, props):
        self.core.board = self
        log.info("BOARD ID: {}".format(self.board_id))
        log.info(f"Config: {props}")
        for config in props.configs:
            log.info(f"Add Config params to module: {config}")
            self.name = self.name = config.get('name', "")
            log.info(f"Name: {self.name}")



