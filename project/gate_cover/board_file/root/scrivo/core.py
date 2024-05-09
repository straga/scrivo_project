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

    def __init__(self, part_name):
        Core._core = self
        self.part_name = part_name
        self.mbus = MbusManager(self)
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

    def cron(self, name, act, interval, unit="sec", *args, **kwargs):
        _act = act(*args, **kwargs)
        if is_coro(_act):
            self._job_list.append(Job(name, act, interval, unit, *args, **kwargs))
        else:
            log.error(f"Job: {name} - {act} - act is not coroutine")

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

                    elif job.unit == "date":
                        current_date = time.localtime()
                        if current_date > job.interval:
                            self.last_run = current_date
                            act = job.act
                            if job.period is not None:
                                if job.period == "day":
                                    job.interval = job.interval[2] + 1
                                elif job.period == "week":
                                    job.interval = job.interval[2] + 7
                                elif job.period == "month":
                                    job.interval = job.interval[1] + 1
                                elif job.period == "year":
                                    job.interval = job.interval[0] + 1
                            else:
                                job.unit = "STOP"

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
    def __init__(self, name, act, interval, unit="sec", *args, **kwargs):
        self.name = name
        self.act = act
        self.interval = interval
        self.unit = unit
        self.args = args
        self.kwargs = kwargs
        self.status = False
        self.period = None
        self.last_run = None

        if isinstance(interval, tuple):
            # check if inteval less that 9, create new interval with 9 elements
            if len(interval) < 9:
                interval = list(interval)
                interval.extend([0] * (9 - len(interval)))
                interval = tuple(interval)

            self.interval = time.mktime(interval)
            self.period = unit
            self.unit = "date"

    def __str__(self):
        return f"{self.name}: {self.interval} {self.unit}"

    def __repr__(self):
        return f"{self.name}: {self.interval} {self.unit}"

    async def start(self):
        self.status = True
        try:
            await self.act(*self.args, **self.kwargs)
        except Exception as e:
            log.error(f"Job: {self.name} - {e}")
        #await self.act(*self.args, **self.kwargs)
        self.status = False

