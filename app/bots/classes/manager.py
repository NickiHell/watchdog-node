from multiprocessing import Process
from typing import Tuple, Dict

from loguru import logger

from app.bots.classes.base import AbstractProcessManager


class BotProcessManager(AbstractProcessManager):
    def __init__(self, bots: Tuple[Tuple[str, callable], ...]):
        self._bots: Tuple[Tuple[str, callable], ...] = bots
        self._processes: Dict[str, Process] = {k[0]: None for k in self._bots}
        self._make_processes()

    async def execute(self):
        await self._start_processes()

    async def _start_processes(self):
        [x.start() for x in self._processes.values()]

    async def _check_processes(self):
        for process in self._processes.values():
            if not process.is_alive():
                # process.start() # TODO: Instancing
                logger.warning(f'Bot process: {process.pid} dead, restarting...')

    def _make_processes(self):
        for bot in self._bots:
            self._processes[bot[0]] = Process(name=f'Bot -> {bot[0]}')
