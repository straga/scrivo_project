# Copyright (c) 2024 Viktor Vorobjov
import machine
from microdot import Microdot, redirect, send_file
from scrivo.module import Module
from scrivo.platform import launch

from scrivo import logging
log = logging.getLogger("WWW")

app = Microdot()

class Runner(Module):




    def activate(self, props):

        log.info(f"Config: {props}")
        for config in props.configs:
            log.info(f"Add Config params to module: {config}")

        launch(app.run, debug=True)


    @app.route('/', methods=['GET', 'POST'])
    def index(self, request):
        form_cookie = None
        message_cookie = None
        if request.method == 'POST':
            form_cookie = '{pin},{pull}'.format(pin=request.form['pin'],
                                                pull=request.form['pull'])
            if 'read' in request.form:
                pull = None
                if request.form['pull'] == 'pullup':
                    pull = machine.Pin.PULL_UP
                elif request.form['pull'] == 'pulldown':
                    pull = machine.Pin.PULL_DOWN
                pin = machine.Pin(int(request.form['pin']), machine.Pin.IN, pull)
                message_cookie = 'Input pin {pin} is {state}.'.format(
                    pin=request.form['pin'],
                    state='high' if pin.value() else 'low')
            else:
                pin = machine.Pin(int(request.form['pin']), machine.Pin.OUT)
                value = 0 if 'set-low' in request.form else 1
                pin.value(value)
                message_cookie = 'Output pin {pin} is now {state}.'.format(
                    pin=request.form['pin'],
                    state='high' if value else 'low')
            response = redirect('/')
        else:
            if 'message' not in request.cookies:
                message_cookie = 'Select a pin and an operation below.'

            print('send_file')
            response = send_file('gpio.html')
        if form_cookie:
            response.set_cookie('form', form_cookie)
        if message_cookie:
            response.set_cookie('message', message_cookie)
        return response





