import functools
from typing import NoReturn

from redis import Redis
from rq import Queue, Retry
from rq.job import Job
from loguru import logger
from rclpy import spin


class Scheduler:
    def __init__(self):
        self._queue = Queue(connection=Redis())
        self._jobs = []


    async def schedule(self, items: list[tuple]) -> None:
        for item in items:
            func = functools.partial(spin, item[0])
            job: Job = self._queue.enqueue(func, retry=Retry(max=5, interval=30))
            self._jobs.append(job)
            logger.debug(f'Enqueue job: {job}, Jobs: {self._jobs}')


    async def check_jobs(self) -> None | NoReturn:
        for job in self._jobs:
            if job.is_finished:
                logger.debug(f'Job {job} is finished!')
                del job
