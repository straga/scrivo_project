
class Switch:

    def __init__(self, pin, name):

        self.name = name
        self.pin = pin
        self.cb = None
        self.state = None
        self.restore = None

    def get_state(self):
        self.state = self.pin.value()
        return self.state

    def call_cb(self):
        if self.cb:
            self.cb(self)

    def change_state(self, _set=None):

        if _set == -1 and self.state is not None:
            self.pin.value(self.state)
        elif _set is not None and isinstance(_set, int):
            self.pin.value(_set)
        elif _set is None:
            self.pin.value(1 - self.pin.value())
        else:
            return

        self.state = self.pin.value()
        self.call_cb()
        return self.state


