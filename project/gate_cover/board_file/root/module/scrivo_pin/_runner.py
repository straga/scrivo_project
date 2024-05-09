

from scrivo.module import Module


from scrivo import logging
log = logging.getLogger("PIN")



class Runner(Module):

    _pins = {}

    def activate(self, props):

        for config in props.configs:

            if config.get("platform") and config.get("platform") == "gpio":
                log.info(f" Config: {config}")

                from .gpio import PinInit
                config["platform"] = PinInit
                self._pins[config["id"]] = config

        #log.debug(f"Pins: {self._pins}")

    # Get and initialize pin
    def get_pin(self, pin_id, value=None):

        pin = self._pins.get(pin_id, None)
        if pin and isinstance(pin, dict):
            config = pin
            platform = config.get("platform")
            if value is not None:
                config["value"] = value
            pin = platform(pin_id, config)
            self._pins[pin_id] = pin

        return pin


