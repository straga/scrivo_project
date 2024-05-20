# Copyright (c) Viktor Vorobjov

import asyncio
import time
from scrivo.platform import launch, is_coro
from scrivo.mbus import MbusManager
from scrivo import logging
log = logging.getLogger("CORE")


class Env:
    def __init__(self):
        self._env = {}

    def __call__(self, name=None):
        if name:
            return self._env.get(name)
        else:
            return self._env

    def set(self, name, action):
        if self._env.get(name):
            log.error("Env: {} - Already Exist".format(name))
        else:
            self._env[name] = action


class Core:
    _core = None
    _board = None
    _job_list = []

    def __init__(self, part_name, maxsize=None):
        Core._core = self
        self.part_name = part_name
        self.mbus = MbusManager(self, maxsize=maxsize)
        self.env = Env()
        launch(self._cron_job)

    def __class__(self):
        return Core._core

    @staticmethod
    def core():
        return Core._core

    @staticmethod
    def board():
        return Core._board

    def cron(self, name, act, interval, unit="sec", period=None, *args, **kwargs):
        self._job_list.append(Job(name, act, interval, unit, period, *args, **kwargs))


    async def _cron_job(self):
        period = 0
        while True:
            # Periodic actions
            for job in self._job_list:
                try:
                    act = None
                    if job.unit == "sec":
                        if period % job.interval == 0:
                            act = job.act
                    elif job.unit == "min":
                        if period % (60 * job.interval) == 0:
                            act = job.act

                    elif job.unit in ["day", "week", "month", "year"]:
                        if time.time() > job.ms:
                            self.last_run = time.localtime()
                            act = job.act
                            if job.unit == "day":
                                job.period[2] = job.period[2] + job.interval
                                job.ms = time.mktime(job.period)

                    if act is not None and not job.status:
                        launch(job.start)
                except Exception as e:
                    log.error(f"TELEMETRY: {e}, {job}")
                await asyncio.sleep(0.01)

            period += 1
            if period > 216000:
                period = 0
            await asyncio.sleep(1)


class Job:
    def __init__(self, name, act, interval, unit="sec", period=None, *args, **kwargs):
        self.name = name
        self.act = act
        self.interval = interval

        self.unit = unit
        self.args = args
        self.kwargs = kwargs
        self.status = False

        self.last_run = None
        tz = 3

        # core.cron('My Job', my_job, 1, 'day', (24,00))

        self.period = None
        self.ms = None

        if unit == "day" and period is not None:
            today = list(time.localtime())
            # (2024, 5, 16, 12, 19, 1, 3, 137)

            today[3] = today[3] - period[0]
            today[4] = today[4] - period[1]
            today[3] = today[3] - tz
            # Create a new tuple with the modified hour
            self.period = today
            self.ms = time.mktime(today)

        log.info(f"Cron Job: {self}")

    def __str__(self):
        return f"{self.name}: {self.interval} {self.unit} - {self.period}"

    def __repr__(self):
        return self.__str__()

    async def start(self):
        self.status = True
        try:
            _act = self.act(*self.args, **self.kwargs)
            if is_coro(_act):
                await _act
            else:
                log.error(f"Job: {self.name} - act is not coroutine")

            # await self.act(*self.args, **self.kwargs)
        except Exception as e:
            log.error(f"Job: {self.name} - {e}")
        self.status = False

