
from scrivo.dev import Event
from threading import Thread

from scrivo import logging
log = logging.getLogger("THREAD")


class RunInThread(Thread):
    """
    """
    def __init__(self, action, *args, **kwargs):
        """Инициализация потока"""
        log.info("Init:")
        # print("Thread Init")
        Thread.__init__(self)
        self.result = None
        self.event = Event()
        self.action = action
        self._args = args
        self._kwargs = kwargs


    def run(self):
        """Запуск потока"""
        # print("Thread Act Run")
        log.info("Act Run")
        try:
            self.result = self.action(*self._args, **self._kwargs)
        except Exception as e:
            # print("Err: thread Act: {}".format(e))
            log.info("Act: ERROR {}".format(e))
            pass

        self.event.set()
        # print("Thread Act Done")
        log.info("Act: Done")


async def run_in_executer(action, *args, **kwargs):

    thread = RunInThread(action, *args, **kwargs)
    thread.start()
    # print("Wait Event")
    log.info("Executer: Wait Event")
    await thread.event.wait()
    log.info("Executer: Return from thread")
    # print("Return from Thread")
    return thread.result



